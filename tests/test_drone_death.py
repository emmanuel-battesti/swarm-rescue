"""
Death is a state, and what it means depends on what killed the drone.

Two causes are implemented, and they are *not* the same outcome:

- damage: the drone was destroyed by collisions. Its wreck stays on the map and
  stays in the way of nobody -- it is passable, and the sensors do not see it, so
  the surviving drones neither collide with it nor report it.
- kill zone: the drone was destroyed by the map. Its wreck stays a solid obstacle
  and stays visible to the sensors, exactly like before.

That split is easy to get wrong, so each part is pinned here separately. The
tests also cover the procedural spin-down (`DEATH_ANIMATION_STEPS` of eased
rotation), and the fact that the uid view is never touched by it -- the colors of
that view *are* the entity identifiers, so rotating or scaling a sprite there
would corrupt what the lidar reads.
"""

import math
import pathlib
import sys
from types import SimpleNamespace

import arcade
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.utils.constants import (
    DEATH_ANIMATION_PEAK_ZOOM,
    DEATH_ANIMATION_STEPS,
    DEATH_BY_DAMAGE,
    DEATH_BY_KILL_ZONE,
    DEATH_WRECK_ALPHA_HIDDEN,
    DEATH_WRECK_ALPHA_SOLID,
    RANGE_COMMUNICATION,
)


class _ProbeDrone(DroneAbstract):
    """A drone that does nothing: only its death is exercised."""

    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 1.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


def _make_drone():
    """
    Build a drone registered in a throwaway playground, and return both.

    The drone has to be in the playground: `die()` asks it to hide from the
    sensors, and restoring it walks the space and the views.
    """
    playground = ClosedPlayground(size=(400, 300))
    drone = _ProbeDrone()
    playground.add(drone, ((0, 0), 0))
    return playground, drone


def _shapes_in_space(playground, entity):
    """How many of the entity's shapes the physical space actually holds."""
    return len(set(entity.pm_elements) & set(playground.space.shapes))


def _in_uid_view(playground, entity):
    """Whether the uid image carries the entity, i.e. whether sensors see it."""
    return entity in playground.uid_view.sprites


def _display_state(base, playground):
    """
    Run the animation for one more step and return the sprite it paints.

    The display view is faked: `update_sprite()` is what every view calls, and
    the playground under test has no display view at all. Only the object
    identity matters, since that is how the uid view is recognized.
    """
    view = object()
    if playground.uid_view is None:
        view = SimpleNamespace()
    sprite = arcade.Sprite(base._alive_texture)
    base.update_sprite(view, sprite)
    return sprite


def test_a_damage_wreck_is_invisible_to_the_sensors_and_passable():
    """Destroyed by damage: the wreck is scenery, not an obstacle and not a sighting."""
    playground, drone = _make_drone()
    try:
        assert _in_uid_view(playground, drone.base)
        assert _shapes_in_space(playground, drone.base) > 0

        drone.die(DEATH_BY_DAMAGE)

        assert drone.is_dead
        assert drone.death_cause == DEATH_BY_DAMAGE
        assert not _in_uid_view(playground, drone.base)
        assert _shapes_in_space(playground, drone.base) == 0
    finally:
        playground.close_window()


def test_a_kill_zone_wreck_is_still_a_visible_obstacle():
    """Destroyed by the map: the wreck keeps blocking and keeps being reported."""
    playground, drone = _make_drone()
    try:
        drone.die(DEATH_BY_KILL_ZONE)

        assert drone.is_dead
        assert drone.death_cause == DEATH_BY_KILL_ZONE
        assert _in_uid_view(playground, drone.base)
        assert _shapes_in_space(playground, drone.base) > 0
    finally:
        playground.close_window()


def test_a_dead_drone_is_not_controlled_anymore():
    """Commands are dropped: a wreck whose sensors are frozen must not fly on."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_KILL_ZONE)  # still in the space, so it could drift
        drone.receive_commands({"forward": 1.0, "lateral": 0.0,
                                "rotation": 0.0, "grasper": 0})
        playground.step(all_commands={drone: {"forward": 1.0, "lateral": 0.0,
                                             "rotation": 0.0, "grasper": 0}})
        position = (base.position.x, base.position.y)

        for _ in range(5):
            playground.step()

        assert (base.position.x, base.position.y) == position
    finally:
        playground.close_window()


def test_a_reset_drone_is_controlled_again():
    """A drone that came back to life gets its commands computed once more."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        drone.reset()

        playground.step(all_commands={drone: {"forward": 1.0, "lateral": 0.0,
                                             "rotation": 0.0, "grasper": 0}})

        assert base.velocity.x != 0 or base.velocity.y != 0
    finally:
        playground.close_window()


def test_a_dead_drone_does_not_move():
    """A wreck is a wreck: it no longer answers its controls."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        position = (base.position.x, base.position.y)

        for _ in range(5):
            playground.step()

        assert (base.position.x, base.position.y) == position
    finally:
        playground.close_window()


# MARK: - the procedural explosion


def test_the_turn_runs_for_the_given_number_of_steps_and_then_stops():
    """The animation is bounded: it advances one step at a time, then holds."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        assert base._death_animation_step == 0

        for expected in range(1, DEATH_ANIMATION_STEPS):
            playground.step()
            assert base._death_animation_step == expected

        playground.step()
        assert base._death_animation_step == DEATH_ANIMATION_STEPS

        # And it stays there: a wreck does not keep re-exploding.
        playground.step()
        assert base._death_animation_step == DEATH_ANIMATION_STEPS
    finally:
        playground.close_window()


def _turn_of(base, playground):
    """
    The angle the animation has added on top of the body orientation.

    `update_sprite()` writes the body angle first and the animation offset on top
    of it, so the offset is what is left once the body angle is taken off. It is
    the thing that measures the speed of the turn.
    """
    sprite = _display_state(base, playground)
    return (sprite.angle + math.degrees(base._pm_body.angle)) % 360.0


def test_the_fade_shows_what_the_sensors_can_still_see():
    """
    The opacity of a wreck is how the cause of death is read on the map.

    A drone destroyed by damage is taken out of the uid image, so its wreck is
    drawn see-through; a drone destroyed by a kill zone is still in that image, so
    its wreck stays opaque. This is the one place where the picture carries
    something the participant cannot read off the sensors any more.
    """
    for cause, expected, seen_by_sensors in (
            (DEATH_BY_DAMAGE, DEATH_WRECK_ALPHA_HIDDEN, False),
            (DEATH_BY_KILL_ZONE, DEATH_WRECK_ALPHA_SOLID, True)):
        playground, drone = _make_drone()
        base = drone.base
        try:
            drone.die(cause)
            for _ in range(DEATH_ANIMATION_STEPS):
                playground.step()

            assert _display_state(base, playground).alpha == expected
            assert _in_uid_view(playground, base) is seen_by_sensors
        finally:
            playground.close_window()


def test_the_fade_reaches_its_opacity_without_a_jump():
    """
    The wreck fades across the turn rather than snapping to its final opacity.

    Fading only at the end would make a drone pop from solid to see-through on one
    frame, which is the very thing the fade is meant to avoid.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)

        alphas = []
        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()
            alphas.append(_display_state(base, playground).alpha)

        assert alphas[0] > DEATH_WRECK_ALPHA_HIDDEN, "it should start opaque"
        assert alphas[-1] == DEATH_WRECK_ALPHA_HIDDEN
        assert all(later <= earlier
                   for earlier, later in zip(alphas, alphas[1:])), \
            f"the fade should only ever darken, got {alphas}"
    finally:
        playground.close_window()


def test_a_reset_drone_gets_its_colors_back():
    """
    A drone restored by `reset()` must stop looking like a see-through wreck.

    The opacity lives on the sprite each view draws, not on `_base_sprite`, and a
    view reuses the same sprite for the whole run. Resetting only the master
    sprite therefore left every view still showing the wreck.

    The sprite here is kept across the whole sequence on purpose: a view reuses
    one, and building a fresh sprite per call -- what the other tests do -- paints
    the wreck straight over the top and hides this.
    """
    playground, drone = _make_drone()
    base = drone.base
    view = object()  # any display view: the uid one is the only one excluded
    sprite = arcade.Sprite(base._alive_texture)
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(DEATH_ANIMATION_STEPS + 2):
            playground.step()
            base.update_sprite(view, sprite)

        assert sprite.alpha == DEATH_WRECK_ALPHA_HIDDEN, \
            "the wreck must be see-through, or this proves nothing"

        drone.reset()
        base.update_sprite(view, sprite)

        assert sprite.alpha == 255, "a restored drone must be opaque again"
        assert sprite.scale == base._alive_scale
    finally:
        playground.close_window()


def test_a_reset_drone_is_repainted_on_the_next_view():
    """
    Restoring the look only works if a view actually repaints the sprite.

    `PhysicalEntity.needs_sprite_update` is `self._moved or self.movable`, and a
    drone is `movable`, so this is true on every step whatever the drone is doing.
    That is what makes the restore in `update_sprite` enough on its own; if a
    movable entity ever stopped being repainted, this is what would notice.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(DEATH_ANIMATION_STEPS + 2):
            playground.step()

        assert base.needs_sprite_update, "a drone is repainted on every step"
    finally:
        playground.close_window()


def test_the_wreck_is_only_slightly_bigger():
    """
    The zoom is a slight swell, not a doubling.

    A wreck at twice the size read as a different object rather than as a dead
    drone, so it only swells a little and is back to normal when the turn ends.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)

        scales = []
        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()
            scales.append(_display_state(base, playground).scale[0])

        assert max(scales) <= 1.0 + DEATH_ANIMATION_PEAK_ZOOM
        assert max(scales) > 1.0, "the wreck should be slightly bigger while turning"
    finally:
        playground.close_window()


def test_the_rotation_slows_down_and_comes_to_rest():
    """
    The turn is fast at first and more and more slow, and stops on the last step.

    A constant rate would make the wreck freeze mid-turn instead of settling,
    which is what the easing buys. The angle is measured as a per-step increment
    because the sprite angle wraps around.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)

        increments = []
        previous = _turn_of(base, playground)
        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()
            current = _turn_of(base, playground)
            increments.append((current - previous) % 360.0)
            previous = current

        assert all(later < earlier
                   for earlier, later in zip(increments, increments[1:])), \
            f"the turn should slow down all along, got {increments}"
        assert increments[-1] < increments[0]
    finally:
        playground.close_window()


def test_the_wreck_comes_to_rest_the_right_way_up():
    """
    The turn ends on the orientation of the dead sprite, with no snap.

    The wreck is left wherever the last animated step left it -- the animation
    offset is not dropped at rest. The total angle is a whole number of turns for
    this to land back on the dead sprite: a total that was not a multiple of 360
    degrees left the wreck resting upside down.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()
        last_animated = _turn_of(base, playground)

        playground.step()  # the wreck has come to rest

        assert _turn_of(base, playground) == pytest.approx(last_animated)
    finally:
        playground.close_window()


def test_the_wreck_is_back_to_its_normal_size_when_the_turn_ends():
    """The zoom is a swell during the turn, not a lasting change of size."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()

        sprite = _display_state(base, playground)

        assert sprite.scale == pytest.approx(base._alive_scale)
    finally:
        playground.close_window()


def test_the_wreck_settles_on_the_plain_dead_sprite():
    """After the animation, a wreck looks like the dead sprite and nothing more."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(DEATH_ANIMATION_STEPS + 2):
            playground.step()

        sprite = _display_state(base, playground)

        assert sprite.scale == base._alive_scale
        assert sprite.alpha == DEATH_WRECK_ALPHA_HIDDEN
    finally:
        playground.close_window()


def test_the_animation_never_touches_the_uid_view():
    """
    The uid view carries the identifiers in its colors.

    A wreck that faded or grew there would be read by the lidar as something
    else entirely, so the uid sprite must come out untouched.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_KILL_ZONE)  # stays in the uid view, unlike damage
        sprite = playground.uid_view.sprites[base]
        untouched = (sprite.scale, sprite.alpha)

        for _ in range(DEATH_ANIMATION_STEPS):
            playground.step()
            base.update_sprite(playground.uid_view, sprite)

        assert (sprite.scale, sprite.alpha) == untouched
    finally:
        playground.close_window()


def test_a_dead_drone_is_wearing_the_dead_sprite():
    """The wreck is drawn as destroyed, not as a drone that lost its way."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        assert base._base_sprite.texture is base._alive_texture

        drone.die(DEATH_BY_DAMAGE)

        assert base._base_sprite.texture is base._dead_texture
    finally:
        playground.close_window()


def test_leaving_a_kill_zone_does_not_revive_the_drone():
    """
    A drone destroyed by a kill zone stays destroyed after it leaves the zone.

    Leaving the zone used to put the alive sprite back on the drone: the kill zone
    was a visual toggle, so a drone flew out of it looking healthy again while
    being dead. The zone flag now follows the zone and the picture follows the
    drone, which no longer comes back.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        base.set_in_kill_zone(True)
        drone.die(DEATH_BY_KILL_ZONE)
        assert base.in_kill_zone

        for _ in range(3):
            base._kill_zone_collision_this_frame = False
            playground.step()

        assert not base.in_kill_zone, "the drone is out of the zone"
        assert drone.is_dead, "but it does not come back to life"
        assert base._base_sprite.texture is base._dead_texture
    finally:
        playground.close_window()


def test_the_kill_zone_does_not_revive_a_dead_drone():
    """
    The kill zone used to swap the texture back to alive on the next step.

    It was only ever a visual toggle and nothing called it, so a destroyed drone
    came back to life visually while staying dead. `post_step()` now leaves a
    dead drone alone.
    """
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)

        for _ in range(3):
            playground.step()

        assert drone.is_dead
        assert base._base_sprite.texture is base._dead_texture
    finally:
        playground.close_window()


# MARK: - resetting


def test_reset_brings_the_drone_back_to_life():
    """Everything the death changed is put back: status, picture, space and sensors."""
    playground, drone = _make_drone()
    base = drone.base
    try:
        drone.die(DEATH_BY_DAMAGE)
        for _ in range(5):
            playground.step()

        drone.reset()

        assert not drone.is_dead
        assert drone.death_cause is None
        assert base._death_animation_step is None
        assert base._base_sprite.texture is base._alive_texture
        assert _in_uid_view(playground, base)
        assert _shapes_in_space(playground, base) > 0
    finally:
        playground.close_window()


def test_a_wreck_draws_no_sensor_rays(monkeypatch):
    """
    A destroyed drone stops drawing its lidar and semantic rays.

    The rays were still drawn from the wreck, which made it look like a drone
    still looking around. The count is done on the lines actually handed to
    arcade rather than on the switch, because the drawing is what the participant
    sees and the switch is only a means to it.

    This fails if the guard is removed, and also if it is moved onto `_disabled`:
    `pre_step` clears that on every device every step, so the rays would come back
    one step after the death.
    """
    drawn = []
    # Both sensors batch their rays into a ShapeElementList rather than calling
    # `arcade.draw_line`, so the count is taken there.
    real_draw = arcade.shape_list.ShapeElementList.draw

    def counting_draw(self):
        drawn.extend(self.shape_list)
        return real_draw(self)

    monkeypatch.setattr(arcade.shape_list.ShapeElementList, "draw", counting_draw)

    playground, drone = _make_drone()
    try:
        for _ in range(2):
            playground.step()

        drawn.clear()
        drone.lidar().draw()
        drone.semantic().draw()
        alive_rays = len(drawn)

        drone.die(DEATH_BY_DAMAGE)
        drawn.clear()

        for _ in range(3):
            playground.step()
            drone.lidar().draw()
            drone.semantic().draw()

        assert alive_rays > 0, "a live drone does draw rays, or this proves nothing"
        assert drawn == [], "a wreck must not draw any sensor ray"
    finally:
        playground.close_window()


def test_a_dead_drone_reports_its_sensors_as_switched_off():
    """And it holds past the step the drone died on, for both causes."""
    for cause in (DEATH_BY_DAMAGE, DEATH_BY_KILL_ZONE):
        playground, drone = _make_drone()
        try:
            drone.die(cause)
            for _ in range(4):
                playground.step()

                assert drone.lidar().is_switched_off
                assert drone.semantic().is_switched_off
        finally:
            playground.close_window()


def test_a_dead_drone_stops_communicating():
    """
    A wreck has no communicator: it neither sends nor receives, for both causes.

    A drone killed by damage is taken out of the space, so no disabling zone
    touches its communicator any more and the per-step `_disabled` flag goes
    back to False. Reading that flag alone therefore let a damage wreck keep
    talking -- and, with key C, drew its links to the drones still alive. The
    death has to be part of what "disabled" means here, as it is for the sensors.
    """
    for cause in (DEATH_BY_DAMAGE, DEATH_BY_KILL_ZONE):
        playground, drone = _make_drone()
        try:
            drone.die(cause)
            for _ in range(4):
                playground.step()

                assert drone.communicator_is_disabled(), (
                    f"a drone dead by {cause} must report its communicator "
                    f"as disabled"
                )
                assert drone.communicator.send("hello") is None
                assert drone.communicator.comms_in_range == []
        finally:
            playground.close_window()


def test_a_dead_drone_is_not_a_neighbor_for_a_living_one():
    """
    The other direction: the living drone must not list the wreck in range.

    `draw_com()` walks the living drone's `comms_in_range` and draws a line to
    each entry, so a wreck left in that list is exactly what the picture showed:
    a dead drone still linked to a live one.
    """

    class _Neighbor(DroneAbstract):
        def define_message_for_all(self):
            return None

        def control(self):
            return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}

    for cause in (DEATH_BY_DAMAGE, DEATH_BY_KILL_ZONE):
        playground = ClosedPlayground(size=(400, 300))
        wreck = _ProbeDrone()
        alive = _Neighbor()
        try:
            playground.add(wreck, ((0, 0), 0))
            playground.add(alive, ((RANGE_COMMUNICATION / 2, 0), 0))
            playground.step()
            assert alive.communicator.comms_in_range, \
                "the two are in range, or this proves nothing"

            wreck.die(cause)
            for _ in range(4):
                playground.step()

                assert alive.communicator.comms_in_range == [], (
                    f"a living drone must not see a {cause} wreck as a peer"
                )
        finally:
            playground.close_window()


def test_a_zone_still_switches_a_sensor_off_for_one_step_only():
    """
    The per-step flag and the death are two different things.

    `pre_step` clears `_disabled` on every device of every drone, so a zone that
    switched a sensor off must not leave it off -- otherwise the two reasons
    `is_switched_off` covers would blur into one and a drone would never recover
    from driving through a zone.
    """
    playground, drone = _make_drone()
    try:
        drone.lidar().disable()
        assert drone.lidar().is_switched_off

        playground.step()

        assert not drone.lidar().is_switched_off
    finally:
        playground.close_window()


def test_a_reset_drone_switches_its_sensors_back_on():
    playground, drone = _make_drone()
    try:
        drone.die(DEATH_BY_DAMAGE)
        playground.step()

        drone.reset()

        assert not drone.lidar().is_switched_off
        assert not drone.semantic().is_switched_off
    finally:
        playground.close_window()


def test_cleanup_walks_a_dead_drone_without_tripping():
    """
    `cleanup()` removes every entity from every view and from the space.

    A wreck is already half out -- the damage kind was taken out of the space and
    out of the uid view on purpose -- so removal has to tolerate meeting it twice.
    """
    playground, drone = _make_drone()
    drone.die(DEATH_BY_DAMAGE)
    for _ in range(3):
        playground.step()

    playground.cleanup()
    playground.close_window()
