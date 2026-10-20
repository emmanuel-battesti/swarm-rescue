"""
Look at the image the ray sensors actually see.

The lidar and the semantic sensor do not look at the map you watch: they look
at the *uid image*, a picture in which every pixel carries the identifier of
the entity drawn on it. When a sensor reports a hit, this image is the evidence,
and it is not visible anywhere else -- the window draws colors, not uids.

That blind spot has a cost. A drone whose uid survived one frame at the
position it had just left is invisible on screen, in the video, and in the
screenshot, and shows up only as a phantom obstacle the drone then steers
around. This tool renders the uid image, decodes it, names every uid it finds,
and reports the ones that belong to nothing.

Usage
-----
    # Default map, 50 steps, dumps PNGs in the current directory
    python src/swarm_rescue/tools/visualize_uid.py

    # Another map, more steps, chosen output directory
    python src/swarm_rescue/tools/visualize_uid.py --map MapIntermediate01 \
        --steps 200 --out /tmp/uids

    # Look at particular steps, and display them
    python src/swarm_rescue/tools/visualize_uid.py --at 1,10,50 --show

What is written
---------------
For each requested step, in `--out`:

    uid_<step>_raw.png      the uid image, exactly as the sensors read it
    uid_<step>_decoded.png  the same image with one color per uid, so that
                            neighboring entities can be told apart at a
                            glance (raw uids differ in their low byte and all
                            look like the same dark shade)
    uid_<step>_legend.txt   uid, entity name and pixel count, sorted by count

Two things are then checked, and both report nothing when they pass:

- a uid in the image that `playground.get_entity_from_uid` cannot resolve,
  drawn in red: an obstacle no entity owns;
- an entity drawn far from where it actually is, which is what an
  incompletely cleared framebuffer leaves behind -- the copy of a drone at the
  position it has just left, where a lidar ray can still read it.

The second check has a size limit worth knowing. It compares a blob against
where its entity is, so it fires when something moves a long way between two
frames -- a reset, a teleport, a frame that took too long. A drone creeping one
pixel per step leaves a ghost one pixel behind itself, which merges with the
real blob and stays under the tolerance. That case is still visible by eye in
the decoded image, which is half the reason the tool exists.
"""

import argparse
import pathlib
import sys
from typing import List, Optional, Tuple

import cv2
import numpy as np

# Insert the 'src' directory, two levels up from this file, into sys.path so the
# tools can be run directly from a checkout.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from swarm_rescue.maps.map_final_2022_23 import MapFinal2022_23
from swarm_rescue.maps.map_final_2023_24_01 import MapFinal_2023_24_01
from swarm_rescue.maps.map_final_2024_25_01 import MapFinal_2024_25_01
from swarm_rescue.maps.map_final_2025_26_01 import MapFinal_2025_26_01
from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.maps.map_medium_01 import MapMedium01
from swarm_rescue.maps.map_medium_02 import MapMedium02
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.utils import normalize_angle

MAPS = {
    "MapMedium01": MapMedium01,
    "MapMedium02": MapMedium02,
    "MapIntermediate01": MapIntermediate01,
    "MapFinal2022_23": MapFinal2022_23,
    "MapFinal_2023_24_01": MapFinal_2023_24_01,
    "MapFinal_2024_25_01": MapFinal_2024_25_01,
    "MapFinal_2025_26_01": MapFinal_2025_26_01,
}


class _WanderingDrone(DroneAbstract):
    """
    A drone that flies, so that the uid image is not static.

    It stays away from the borders on purpose: a drone stuck against a wall
    stops producing new shapes, and a tool for looking at the uid image is
    most useful when things move.
    """

    def define_message_for_all(self):
        pass

    def control(self) -> CommandsDict:
        angle = normalize_angle(self.measured_compass_angle()
                                - 0.02 * self.elapsed_timestep)
        command: CommandsDict = {"forward": 1.0,
                                 "lateral": 0.0,
                                 "rotation": float(np.clip(2.0 * angle, -1.0, 1.0)),
                                 "grasper": 0}
        return command


def decode_uid_image(image: np.ndarray) -> np.ndarray:
    """
    Turn the uid image into an array of entity identifiers.

    The formula is the one `RayCompute` applies to the very same pixels, copied
    rather than re-derived: `id_to_pixel` builds a color from the uid, and any
    other recombination silently invents uids that belong to nothing.

    Args:
        image: The uid image, of shape (height, width, 3).

    Returns:
        np.ndarray: An array of shape (height, width) holding the uid of the
        entity drawn on each pixel. Zero means "nothing there", which is what
        the sensors read as no hit.
    """
    return (65536 * image[..., 2].astype(np.int64)
            + 256 * image[..., 1].astype(np.int64)
            + image[..., 0].astype(np.int64))


def colorise(uids: np.ndarray,
              the_map: MapAbstract) -> Tuple[np.ndarray, List[Tuple]]:
    """
    Give each uid its own color, so neighboring entities can be told apart.

    Args:
        uids: The decoded uid image, of shape (height, width).
        the_map: The map, used to name whatever uid is found.

    Returns:
        Tuple[np.ndarray, List[Tuple]]: an RGB image, and one
        (uid, entity name, pixel count, color) row per uid found.
    """
    playground = the_map.playground
    assert playground is not None, "The map has not been built."
    values, counts = np.unique(uids, return_counts=True)
    rows = []

    image = np.zeros((*uids.shape, 3), dtype=np.uint8)
    for index, (uid, count) in enumerate(zip(values, counts)):
        uid = int(uid)

        if uid == 0:
            # The uid view is cleared to black, and `RayCompute` reads zero as
            # "first non-zero", i.e. no hit. It is empty space, not a phantom,
            # and flagging it as one would drown the real ones.
            name = "background (no hit)"
            color = (40, 40, 40)
        else:
            # `get_entity_from_uid` is what the sensors resolve a hit through,
            # so asking it the same question is what makes this tool
            # trustworthy: a uid it cannot resolve is one no entity owns.
            entity = playground.get_entity_from_uid(uid)

            if entity is None:
                name = "UNKNOWN (nothing owns this uid)"
                color = (0, 0, 255)      # red
            else:
                name = f"{type(entity).__name__} '{entity.name}'"
                # Golden-ratio hue stepping: consecutive uids stay far apart,
                # and the same uid always gets the same color. OpenCV expects
                # the hue in [0, 179], hence the halving.
                hue = int((index * 137.508) % 360) // 2
                color = _hsv_to_rgb(hue, 0.85, 0.95)

        image[uids == uid] = color
        rows.append((uid, name, int(count), color))

    rows.sort(key=lambda row: -row[2])
    return image, rows


def _hsv_to_rgb(hue: int, saturation: float, value: float) -> Tuple[int, int, int]:
    """Convert an HSV triplet to a BGR one, the order cv2 and the frame use."""
    pixel = np.array([[[hue, saturation * 255, value * 255]]], dtype=np.uint8)
    blue, green, red = cv2.cvtColor(pixel, cv2.COLOR_HSV2BGR)[0][0]
    return int(blue), int(green), int(red)


def find_mislocated(uids: np.ndarray,
                    the_map: MapAbstract,
                    tolerance: float = 25.0) -> List[Tuple]:
    """
    Report the entities drawn somewhere they are not.

    A uid belongs to a live entity, so its blob has to be where that entity is.
    When it is not, the entity is drawn twice, or appears where it is not -- which
    is exactly what an incompletely cleared framebuffer produces, and what makes
    a sensor see an obstacle that is not there.

    Args:
        uids: The decoded uid image, of shape (height, width).
        the_map: The map being inspected.
        tolerance: How far, in pixels, a blob may sit from its entity.

    Returns:
        List[Tuple]: (uid, entity name, expected pixel, drawn pixel, distance)
        for every entity drawn too far from where it is, worst first.
    """
    playground = the_map.playground
    assert playground is not None, "The map has not been built."
    provider = playground.ray_compute.uid_provider
    half_width = provider.width / 2
    half_height = provider.height / 2
    found = []

    for uid in np.unique(uids):
        uid = int(uid)
        if uid == 0:
            continue

        entity = playground.get_entity_from_uid(uid)
        if entity is None:
            continue      # reported separately, as an unknown uid

        if not hasattr(entity, "true_position"):
            # Only the drones publish a true position. Walls and boxes belong to
            # the map, and a drone's base is a body part that has none of its
            # own -- there is nothing to compare a blob against for them.
            continue

        ys, xs = np.nonzero(uids == uid)
        if not len(xs):
            continue

        drawn = (float(xs.mean()), float(ys.mean()))
        world = entity.true_position()
        # `_WorldSpaceProjector` projects with ortho(-w/2, w/2, -h/2, h/2), so
        # the world point (-w/2, -h/2) lands on pixel (0, 0) of the provider's
        # frame. The image dumped is mirrored across the horizontal axis (see
        # `dump_step`), so the y axis of the picture counts *upwards* in world
        # terms: the expected row is measured from the bottom edge.
        expected = (half_width + float(world[0]),
                    half_height - float(world[1]))
        distance = float(np.hypot(drawn[0] - expected[0], drawn[1] - expected[1]))

        if distance > tolerance:
            found.append((uid, f"{type(entity).__name__} '{entity.name}'",
                          expected, drawn, distance))

    found.sort(key=lambda row: -row[4])
    return found


def write_legend(path: pathlib.Path,
                 rows: List[Tuple],
                 step: int,
                 the_map: MapAbstract,
                 mislocated: List[Tuple]) -> None:
    """
    Write the uid table next to the images.

    Args:
        path: The file to write.
        rows: The rows produced by `colorise`.
        step: The simulated step the images were taken at.
        the_map: The map, for the header.
        mislocated: The rows produced by `find_mislocated`.
    """
    lines = [f"uid image legend -- {type(the_map).__name__} -- step {step}",
             f"{'uid':>10}  {'pixels':>8}  {'bgr color':>12}  entity",
             "-" * 64]

    for uid, name, count, color in rows:
        lines.append(f"{uid:>10}  {count:>8}  {str(color):>12}  {name}")

    unknown = [row for row in rows if row[1].startswith("UNKNOWN")]
    lines.append("")
    if unknown:
        lines.append(f"!! {len(unknown)} uid(s) present in the image but absent "
                     f"from the playground:")
        for uid, _, count, _ in unknown:
            lines.append(f"   uid {uid} on {count} pixels")
    else:
        lines.append("Every uid in the image belongs to the playground.")

    lines.append("")
    if mislocated:
        lines.append(f"!! {len(mislocated)} entity(ies) drawn away from where "
                     f"they are:")
        for uid, name, expected, drawn, distance in mislocated:
            lines.append(f"   uid {uid} {name}: expected near "
                         f"({expected[0]:.0f}, {expected[1]:.0f}), drawn at "
                         f"({drawn[0]:.0f}, {drawn[1]:.0f}), {distance:.0f} px away")
    else:
        lines.append("Every entity is drawn where it actually is.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dump_step(the_map: MapAbstract,
              out_dir: pathlib.Path,
              step: int,
              show: bool) -> None:
    """
    Write the raw and decoded uid images for one step.

    Args:
        the_map: The map being inspected.
        out_dir: Where to write; created if missing.
        step: The step number, used in the file names.
        show: Whether to display the images with OpenCV.
    """
    playground = the_map.playground
    assert playground is not None, "The map has not been built."
    provider = playground.ray_compute.uid_provider
    provider.render_uids()
    raw = np.array(provider.read_uid_image())
    # The provider draws the image with its y axis pointing up, while images
    # and pixel indices grow downwards: mirroring across the horizontal axis
    # puts what is at the top of the world at the top of the picture.
    raw = np.flipud(raw)

    uids = decode_uid_image(raw)
    decoded, rows = colorise(uids, the_map)
    mislocated = find_mislocated(uids, the_map)

    # `get_np_img` gives BGR, and so do we, so cv2.imwrite needs no swap.
    cv2.imwrite(str(out_dir / f"uid_{step:04d}_raw.png"), raw)
    cv2.imwrite(str(out_dir / f"uid_{step:04d}_decoded.png"), decoded)
    write_legend(out_dir / f"uid_{step:04d}_legend.txt", rows, step,
                 the_map, mislocated)

    unknown = sum(1 for row in rows if row[1].startswith("UNKNOWN"))
    # The background is always the biggest blob and says nothing; report the
    # biggest entity instead.
    entities = [row for row in rows if not row[1].startswith("background")]
    biggest = entities[0] if entities else None

    print(f"step {step:>4}: {len(entities)} entities, largest "
          f"{biggest[1] if biggest else '-'} on {biggest[2] if biggest else 0} px")
    if unknown:
        print(f"          !! {unknown} uid(s) owned by nobody")
    if mislocated:
        print(f"          !! {len(mislocated)} entity(ies) drawn in the wrong "
              f"place, e.g. {mislocated[0][1]} is {mislocated[0][4]:.0f} px "
              f"from where it is")
    if not unknown and not mislocated:
        print("          no phantom, every entity drawn where it is")

    if show:
        cv2.imshow(f"uid raw step {step}", raw)
        cv2.imshow(f"uid decoded step {step}", decoded)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def parse_steps(requested: Optional[str], nb_steps: int) -> List[int]:
    """
    Decide which steps to dump.

    Args:
        requested: A comma separated list of steps, or None.
        nb_steps: How many steps the run goes through.

    Returns:
        List[int]: The steps to dump.
    """
    if not requested:
        # The first steps show the sensors warming up, the last one shows the
        # end state; the middle is where a phantom is easiest to miss.
        return sorted({1, nb_steps // 2, nb_steps})

    return sorted({int(part) for part in requested.split(",") if part.strip()})


def main():
    parser = argparse.ArgumentParser(
        description="Visualize the uid image the ray sensors read.")
    parser.add_argument("--map", "-m", default="MapMedium01",
                        choices=sorted(MAPS),
                        help="Map to inspect (default: MapMedium01)")
    parser.add_argument("--steps", "-n", type=int, default=50,
                        help="Number of steps to simulate (default: 50)")
    parser.add_argument("--at", default=None,
                        help="Comma separated steps to dump "
                             "(default: first, middle and last)")
    parser.add_argument("--out", default="uid_dump",
                        help="Output directory (default: uid_dump)")
    parser.add_argument("--show", action="store_true",
                        help="Display the images instead of only writing them")
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    the_map = MAPS[args.map](drone_type=_WanderingDrone)
    playground = the_map.playground
    assert playground is not None, "The map has not been built."
    playground.step()              # builds the uid image and the sensors
    wanted = parse_steps(args.at, args.steps)

    print(f"{args.map}: {the_map.number_drones} drone(s), "
          f"{the_map.number_wounded_persons} wounded, "
          f"uid image {playground.ray_compute.uid_provider.width}"
          f"x{playground.ray_compute.uid_provider.height}")
    print(f"dumping steps {wanted} into {out_dir}/\n")

    try:
        for step in range(1, args.steps + 1):
            if step in wanted:
                dump_step(the_map, out_dir, step, args.show)
            if step < args.steps:
                playground.step()
    finally:
        playground.cleanup()
        playground.close_window()


if __name__ == '__main__':
    main()
