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
                float center_view_x = ViewParams.center_view_x;
                float center_view_y = ViewParams.center_view_y;
                float zoom = ViewParams.zoom;
                float view_w = ViewParams.w;
                float view_h = ViewParams.h;

                // SENSOR POSITION
                Coordinate in_coord = In.coords[i_sensor];
                float sensor_pos_x = in_coord.pos_x;
                float sensor_pos_y = in_coord.pos_y;

                float sensor_x_on_view = (sensor_pos_x - center_view_x)*zoom + view_w/2;
                float sensor_y_on_view = (sensor_pos_y - center_view_y)*zoom + view_h/2;

                float angle = in_coord.angle;

                // INVISIBLE POINTS
                int inv_pts[MAX_N_INVISIBLE] = InvIDs.inv_ids[i_sensor];

                // CENTER AND END OF RAY
                vec2 center = vec2(sensor_x_on_view, sensor_y_on_view);
                vec2 end_pos = vec2(
                        sensor_x_on_view + range*cos(angle -fov/2 + i_ray*fov/(n_rays-1))*zoom,
                        sensor_y_on_view + range*sin(angle -fov/2 + i_ray*fov/(n_rays-1))*zoom);

                // OUTPUTS
                ivec2 sample_point = ivec2(0,0);
                vec4 id_color_out = vec4(0,0,0,0);
                int id_out = 0;

                // Ray cast
                for(float i=0; i<n_points; i++)
                {
                    float ratio = i/n_points;
                    sample_point = ivec2(mix(center, end_pos, ratio));
                    id_color_out = texelFetch(id_texture, sample_point, 0);

                    id_out = int(256*256*id_color_out.z*255 + 256*id_color_out.y*255 + id_color_out.x*255);

                    if (id_out != 0)
                    {
                        bool invisible = false;

                        for(int ind_inv=0; ind_inv<MAX_N_INVISIBLE; ind_inv++)
                        {
                            if (inv_pts[ind_inv] == id_out)
                            {
                                invisible = true;
                                id_out = 0;
                                break;
                            }

                        }

                        if (!invisible)
                        {
                            break;
                        }

                    }

                }

                float dist = range;
                if (id_out != 0)
                {
                    float dx = sample_point.x - sensor_x_on_view;
                    float dy = sample_point.y - sensor_y_on_view;
                    dist = sqrt( (dx*dx) + (dy*dy) )/zoom;
                }
                // CONVERT IN THE FRAME OF THE ENVIRONMENT

                HitPoint out_pt;

                out_pt.view_pos_x = sample_point.x;
                out_pt.view_pos_y = sample_point.y;

                out_pt.env_pos_x = (sample_point.x - view_w/2)/zoom + center_view_x ;
                out_pt.env_pos_y = (sample_point.y - view_h/2)/zoom + center_view_y ;

                //float rel_pos_x = (sample_point.x - center_x)*cos(angle) - (sample_point.y - center_y)*sin(angle);
                //out_pt.env_rel_pos_x = rel_pos_x/zoom;

                //float rel_pos_y = (sample_point.y - center_y)*cos(angle) + (sample_point.x - center_x)*sin(angle);
                //out_pt.env_rel_pos_y = rel_pos_y/zoom;

                out_pt.sensor_x_on_view = sensor_x_on_view ;
                out_pt.sensor_y_on_view = sensor_y_on_view ;

                out_pt.id = float(id_out);
                out_pt.dist = dist/zoom;

                Out.hpts[i_ray + i_sensor*MAX_N_RAYS] = out_pt;

            }

