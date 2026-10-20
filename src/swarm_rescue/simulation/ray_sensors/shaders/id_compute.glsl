            #version 440

            layout(local_size_x=MAX_N_RAYS) in;

            struct HitPoint
            {
                // Position of hitpoint on view
                float view_pos_x;
                float view_pos_y;

                // Position of hitpoint in env
                float env_pos_x;
                float env_pos_y;

                // Position of hitpoint relative to sensor
                float rel_pos_x;
                float rel_pos_y;

                // Position of sensor on view
                float sensor_x_on_view;
                float sensor_y_on_view;

                float id;
                float dist;
            };

            struct SensorParam
            {
                float range;
                float fov;
                float n_rays;
                float n_points;
            };

            struct Coordinate
            {
                float pos_x;
                float pos_y;
                float angle;
            };

            uniform sampler2D id_texture;

            layout(std430, binding = 2) buffer sparams
            {
                SensorParam sensor_params[N_SENSORS];
            } Params;

            layout(std430, binding = 3) buffer coordinates
            {
                Coordinate coords[N_SENSORS];
            } In;

            layout(std430, binding = 4) buffer hit_points
            {
                HitPoint hpts[];
            } Out;

            layout(std430, binding=5) buffer invisible_ids
            {
                int inv_ids[N_SENSORS][MAX_N_INVISIBLE];
            }InvIDs;

            layout(std430, binding=6) buffer view_params
            {
                float center_view_x;
                float center_view_y;
                float w;
                float h;
                float zoom;

            }ViewParams;

            //float pi = 3.141592;

            void main() {

                int i_ray = int(gl_LocalInvocationIndex);
                int i_sensor = int(gl_WorkGroupID);

                // SENSOR PARAMETERS
                SensorParam s_param = Params.sensor_params[i_sensor];
                float range = s_param.range;
                float fov = s_param.fov;
                float n_rays = s_param.n_rays;
                float n_points = s_param.n_points;

                // VIEW PARAMETERS
                // The uid image is world-space, so only its size is needed: the
                // half-size offset below is the whole world -> pixel mapping.
                // `center_view_x/y` and `zoom` are still declared in the block
                // above to keep the std430 layout the CPU side writes.
                float view_w = ViewParams.w;
                float view_h = ViewParams.h;

                // SENSOR POSITION
                Coordinate in_coord = In.coords[i_sensor];
                float angle = in_coord.angle;

                // The uid image is rendered with a world-space projection
                // (ortho(-w/2, w/2, -h/2, h/2), see TopDownView), so a world
                // point and its pixel differ only by the constant (w/2, h/2).
                // Everything below is therefore computed in WORLD units and the
                // conversion to a pixel happens once, at the texelFetch.
                vec2 center = vec2(in_coord.pos_x, in_coord.pos_y);

                // INVISIBLE POINTS
                int inv_pts[MAX_N_INVISIBLE];
                for (int j = 0; j < MAX_N_INVISIBLE; j++)
                {
                    inv_pts[j] = InvIDs.inv_ids[i_sensor][j];
                }

                // CENTER AND END OF RAY, in world units
                float angle_step = (n_rays > 1) ? fov/(n_rays-1): 0.0;
                vec2 end_pos = center + range*vec2(
                        cos(angle -fov/2 + i_ray*angle_step),
                        sin(angle -fov/2 + i_ray*angle_step));

                // BOUNDS OF THE VIEW TEXTURE, USED TO CLAMP SAMPLE POINTS
                ivec2 view_max = ivec2(int(view_w) - 1, int(view_h) - 1);

                // OUTPUTS
                ivec2 sample_point = ivec2(0,0);
                vec4 id_color_out = vec4(0,0,0,0);
                int id_out = 0;
                // World position of the sample that produced `id_out`. Kept
                // alongside the pixel so the hitpoint can be reported in world
                // units without reading the texture position back.
                vec2 hit_world_from_sample = end_pos;

                // Ray cast, in world units. The only world -> pixel step is the
                // half-size offset added here to index the texture.
                for(float i=0; i<n_points; i++)
                {
                    float ratio = i/n_points;
                    vec2 world_point = mix(center, end_pos, ratio);
                    vec2 pixel_point = world_point + vec2(view_w/2, view_h/2);
                    sample_point = clamp(ivec2(pixel_point), ivec2(0), view_max);
                    id_color_out = texelFetch(id_texture, sample_point, 0);

                    id_out = int(256*256*id_color_out.z*255 + 256*id_color_out.y*255 + id_color_out.x*255);

                    if (id_out != 0)
                    {
                        bool invisible = false;

                        for(int ind_inv=0; ind_inv<MAX_N_INVISIBLE; ind_inv++)
                        {
                            // The id is rebuilt from three 8-bit channels, so it
                            // spans up to 2^24. Above 2^23 a float32 cannot hold
                            // every integer, and some drivers (Mesa llvmpipe,
                            // software rendering under xvfb) hand back a texel
                            // that is off by one unit. Strict equality would
                            // then miss the invisible entity -- the drone base
                            // is centered on the sensor, so the ray would report
                            // a hit at distance 0 and every lidar value would
                            // collapse. Tolerating one unit on this comparison
                            // only costs a hair of extra masking, and never
                            // turns a visible entity invisible unless its uid
                            // happens to sit one away from an invisible one.
                            if (abs(inv_pts[ind_inv] - id_out) <= 1)
                            {
                                invisible = true;
                                id_out = 0;
                                break;
                            }

                        }

                        if (!invisible)
                        {
                            hit_world_from_sample = world_point;
                            break;
                        }

                    }

                }

                // The hitpoint, in world units. A ray that hit nothing has id_out == 0 and
                // is reported at its full range, i.e. at the end of the ray.
                vec2 hit_world = (id_out != 0) ? hit_world_from_sample: end_pos;

                float dist = range;
                if (id_out != 0)
                {
                    dist = length(hit_world - center);
                }

                HitPoint out_pt;

                // Columns 0:2 and 2:4 are both the world position of the
                // hitpoint. They used to differ (0:2 in view pixels, 2:4 in
                // world); with a world-space uid image they are the same value.
                // Both are kept so the layout still matches the CPU path.
                out_pt.view_pos_x = hit_world.x;
                out_pt.view_pos_y = hit_world.y;

                out_pt.env_pos_x = hit_world.x;
                out_pt.env_pos_y = hit_world.y;

                out_pt.rel_pos_x = 0.0;
                out_pt.rel_pos_y = 0.0;

                // Sensor position, in world units.
                out_pt.sensor_x_on_view = center.x ;
                out_pt.sensor_y_on_view = center.y ;

                out_pt.id = float(id_out);
                out_pt.dist = dist;

                Out.hpts[i_ray + i_sensor*MAX_N_RAYS] = out_pt;

            }

