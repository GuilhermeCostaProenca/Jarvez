extends Node3D

@export var core_mesh_path: NodePath
@export var ring_mesh_path: NodePath
@export var ring2_mesh_path: NodePath
@export var shell_mesh_path: NodePath
@export var camera_path: NodePath
@export var debug_label_path: NodePath

@onready var core: MeshInstance3D = get_node_or_null(core_mesh_path)
@onready var ring: MeshInstance3D = get_node_or_null(ring_mesh_path)
@onready var ring2: MeshInstance3D = get_node_or_null(ring2_mesh_path)
@onready var shell: MeshInstance3D = get_node_or_null(shell_mesh_path)
@onready var cam: Camera3D = get_node_or_null(camera_path)
@onready var debug_label: Label = get_node_or_null(debug_label_path)
@onready var state_bus: Node = $StateBus

var current_state := "idle"
var current_intensity := 0.5
var current_mood := "calm"

var drag_active := false
var rot_velocity := Vector2.ZERO
var mouse_push := 0.0
var time_accum := 0.0
var rng := RandomNumberGenerator.new()

# Drift targets for layers (yaw offsets) and timers for occasional realign.
var ring_target := 0.0
var ring2_target := 0.0
var shell_target := 0.0
var ring_phase := 0.0
var ring2_phase := 0.0
var shell_phase := 0.0
var next_realign_at := 2.5

# Slow “attention” focus between perception (cyan) and reasoning (amber).
var focus_mix := 0.0 # 0 = cyan/perception, 1 = amber/reasoning
var focus_target := 0.0
var next_focus_shift_at := 6.0

# Layer emphasis to make hierarchy uneven.
var core_emph := 1.0
var ring_emph := 1.0
var shell_emph := 1.0
var core_target := 1.0
var ring_target_emph := 1.0
var shell_target_emph := 1.0
var next_emph_shift_at := 7.0

# Layer-specific temporal offsets (no sync).
var core_time_scale := 1.0
var ring_time_scale := 1.0
var ring2_time_scale := 1.0
var shell_time_scale := 1.0

const STATE_PRESETS := {
	"idle":      {"spin": 0.05, "pulse": 0.05, "tilt": 0.02},
	"listening": {"spin": 0.12, "pulse": 0.08, "tilt": 0.05},
	"thinking":  {"spin": 0.16, "pulse": 0.10, "tilt": 0.06},
	"speaking":  {"spin": 0.22, "pulse": 0.14, "tilt": 0.08},
	"intense":   {"spin": 0.3,  "pulse": 0.18, "tilt": 0.10},
}

const MOOD_COLORS := {
	"calm": Color(0.30, 0.85, 1.00, 1.0),
	"focus": Color(0.35, 1.00, 0.90, 1.0),
	"warm": Color(1.00, 0.70, 0.35, 1.0),
	"alert": Color(1.00, 0.45, 0.35, 1.0),
	"intense": Color(1.00, 0.35, 0.20, 1.0)
}


func _ready() -> void:
	if state_bus:
		state_bus.connect("state_changed", Callable(self, "_on_state_changed"))
		state_bus.connect("intensity_changed", Callable(self, "_on_intensity_changed"))
		state_bus.connect("mood_changed", Callable(self, "_on_mood_changed"))
	rng.randomize()
	_reset_realign_timer()
	_reset_focus_timer()
	_reset_emph_timer()
	_set_time_scales()
	_apply_state(true)


func _process(delta: float) -> void:
	time_accum += delta
	_update_focus(delta)
	_update_emphasis(delta)
	_update_mouse_push()
	_update_rotation(delta)
	_update_motion(delta)
	_update_materials()
	_update_debug()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			drag_active = mb.pressed
			rot_velocity = Vector2.ZERO
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_nudge_intensity(0.05)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_nudge_intensity(-0.05)
	elif event is InputEventMouseMotion and drag_active:
		var mm := event as InputEventMouseMotion
		rot_velocity += mm.relative * 0.005


func _nudge_intensity(amount: float) -> void:
	current_intensity = clamp(current_intensity + amount, 0.0, 1.0)
	_apply_state()


func _on_state_changed(new_state: String) -> void:
	current_state = new_state
	_apply_state()


func _on_intensity_changed(value: float) -> void:
	current_intensity = clamp(value, 0.0, 1.0)
	_apply_state()


func _on_mood_changed(value: String) -> void:
	current_mood = value
	_apply_state()


func _update_rotation(delta: float) -> void:
	if drag_active:
		rotation.x += rot_velocity.y * delta
		rotation.y += rot_velocity.x * delta
	# Inertia with resistance to feel weighty.
	rot_velocity = rot_velocity.lerp(Vector2.ZERO, clamp(2.0 * delta, 0.0, 1.0))


func _update_motion(delta: float) -> void:
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var spin_base: float = preset["spin"] * 0.05 + current_intensity * 0.02
	var pulse_amp: float = preset["pulse"] * 0.4 + current_intensity * 0.03
	var tilt_amp: float = preset["tilt"] * 0.4 + mouse_push * 0.02

	rotation.y += spin_base * delta
	rotation.x = sin(time_accum * 0.4 * core_time_scale) * tilt_amp

	# Occasional realignments rather than constant spin.
	if time_accum >= next_realign_at:
		_set_new_targets()

	if ring:
		var r_yaw := ring.rotation.y
		ring.rotation.y = lerp_angle(r_yaw, ring_target + sin(time_accum * ring_time_scale + ring_phase) * 0.03, clamp(delta * 0.2, 0.0, 1.0))
	if ring2:
		var r2_yaw := ring2.rotation.y
		ring2.rotation.y = lerp_angle(r2_yaw, ring2_target + sin(time_accum * ring2_time_scale * 0.7 + ring2_phase) * 0.025, clamp(delta * 0.18, 0.0, 1.0))
	if shell:
		var s_yaw := shell.rotation.y
		shell.rotation.y = lerp_angle(s_yaw, shell_target + sin(time_accum * shell_time_scale * 0.5 + shell_phase) * 0.02, clamp(delta * 0.15, 0.0, 1.0))

	var bob := sin(time_accum * 0.3 * core_time_scale) * pulse_amp * 0.15
	position.y = bob


func _update_mouse_push() -> void:
	if cam == null:
		mouse_push = 0.0
		return
	var screen_pos: Vector2 = cam.unproject_position(global_transform.origin)
	var mouse_pos: Vector2 = get_viewport().get_mouse_position()
	var dist: float = mouse_pos.distance_to(screen_pos)
	# Presence of user has minimal effect; only slight influence.
	mouse_push = clamp((1.0 - dist / 480.0) * 0.2, 0.0, 0.2)


func _update_materials() -> void:
	var color := _focused_color()
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var spin_mod: float = preset["spin"]

	if core:
		var mat := core.material_override
		if mat is ShaderMaterial:
			mat.set_shader_parameter("core_color", color * core_emph)
			mat.set_shader_parameter("edge_color", Color(1, 1, 1, 0.9))
			mat.set_shader_parameter("intensity", (0.18 + current_intensity * 0.35 + mouse_push * 0.1) * core_emph)
			mat.set_shader_parameter("pulse", 0.05 + current_intensity * 0.12)
			if current_state == "thinking":
				mat.set_shader_parameter("grid_scale", 12.0 + current_intensity * 4.0)
			else:
				mat.set_shader_parameter("grid_scale", 8.0 + current_intensity * 3.0)

	if ring:
		var rmat := ring.material_override
		if rmat is ShaderMaterial:
			rmat.set_shader_parameter("ring_color", color * ring_emph)
			rmat.set_shader_parameter("intensity", (0.12 + current_intensity * 0.25) * ring_emph)
			rmat.set_shader_parameter("scroll_speed", 0.05 + spin_mod * 0.3)

	if ring2:
		var r2mat := ring2.material_override
		if r2mat is ShaderMaterial:
			var warm_mix := color.lerp(Color(1.0, 0.8, 0.5, 1.0), 0.3)
			r2mat.set_shader_parameter("ring_color", warm_mix * ring_emph)
			r2mat.set_shader_parameter("intensity", (0.1 + current_intensity * 0.2) * ring_emph)
			r2mat.set_shader_parameter("scroll_speed", -0.05 - spin_mod * 0.25)
			r2mat.set_shader_parameter("line_density", 18.0 + current_intensity * 4.0)

	if shell:
		var smat := shell.material_override
		if smat is ShaderMaterial:
			smat.set_shader_parameter("energy_color", color * shell_emph)
			smat.set_shader_parameter("intensity", (0.1 + current_intensity * 0.18) * shell_emph)
			smat.set_shader_parameter("grid_scale", 12.0 + current_intensity * 4.0)
			smat.set_shader_parameter("grid_thickness", 0.008 + mouse_push * 0.006)
			smat.set_shader_parameter("scan_speed", 0.08 + spin_mod * 0.2)


func _update_debug() -> void:
	if debug_label:
		var ws_ok := false
		if state_bus and state_bus.has_method("ws_is_connected"):
			ws_ok = state_bus.call("ws_is_connected")
		var ws_label := "ok" if ws_ok else "down"
		debug_label.text = "state: %s | intensity: %.2f | ws: %s" % [current_state, current_intensity, ws_label]


func _apply_state(_immediate: bool = false) -> void:
	_update_materials()
	_update_debug()


func _mood_color() -> Color:
	if MOOD_COLORS.has(current_mood):
		return MOOD_COLORS[current_mood]
	return MOOD_COLORS["calm"]


func _focused_color() -> Color:
	# Blend cyan (perception) to amber (reasoning) slowly via focus_mix.
	var perception := Color(0.30, 0.85, 1.00, 1.0)
	var reasoning := Color(1.00, 0.70, 0.35, 1.0)
	return perception.lerp(reasoning, focus_mix)


func _reset_realign_timer() -> void:
	next_realign_at = time_accum + rng.randf_range(10.0, 18.0)
	ring_phase = rng.randf_range(-PI, PI)
	ring2_phase = rng.randf_range(-PI, PI)
	shell_phase = rng.randf_range(-PI, PI)


func _set_new_targets() -> void:
	# Small intentional drifts; no constant spin.
	ring_target += rng.randf_range(-0.25, 0.25)
	ring2_target += rng.randf_range(-0.2, 0.2)
	shell_target += rng.randf_range(-0.15, 0.15)
	_reset_realign_timer()


func _reset_focus_timer() -> void:
	next_focus_shift_at = time_accum + rng.randf_range(12.0, 22.0)
	focus_target = clamp(focus_mix + rng.randf_range(-0.15, 0.15), 0.0, 1.0)


func _update_focus(delta: float) -> void:
	if time_accum >= next_focus_shift_at:
		_reset_focus_timer()
	focus_mix = lerp(focus_mix, focus_target, clamp(delta * 0.02, 0.0, 1.0))


func _reset_emph_timer() -> void:
	next_emph_shift_at = time_accum + rng.randf_range(14.0, 26.0)
	core_target = rng.randf_range(0.9, 1.1)
	ring_target_emph = rng.randf_range(0.85, 1.15)
	shell_target_emph = rng.randf_range(0.8, 1.15)
	_set_time_scales()


func _update_emphasis(delta: float) -> void:
	if time_accum >= next_emph_shift_at:
		_reset_emph_timer()
	core_emph = lerp(core_emph, core_target, clamp(delta * 0.03, 0.0, 1.0))
	ring_emph = lerp(ring_emph, ring_target_emph, clamp(delta * 0.03, 0.0, 1.0))
	shell_emph = lerp(shell_emph, shell_target_emph, clamp(delta * 0.03, 0.0, 1.0))


func _set_time_scales() -> void:
	core_time_scale = rng.randf_range(0.85, 1.05)
	ring_time_scale = rng.randf_range(0.75, 1.0)
	ring2_time_scale = rng.randf_range(0.7, 0.95)
	shell_time_scale = rng.randf_range(0.65, 0.9)
