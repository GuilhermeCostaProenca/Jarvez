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
	_apply_state(true)


func _process(delta: float) -> void:
	time_accum += delta
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
	rot_velocity = rot_velocity.lerp(Vector2.ZERO, clamp(3.0 * delta, 0.0, 1.0))


func _update_motion(delta: float) -> void:
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var spin_base: float = preset["spin"] + current_intensity * 0.1
	var pulse_amp: float = preset["pulse"] + current_intensity * 0.05
	var tilt_amp: float = preset["tilt"] + mouse_push * 0.1

	rotation.y += spin_base * delta
	rotation.x = sin(time_accum * 0.6) * tilt_amp

	if ring:
		ring.rotate_y(spin_base * 1.4 * delta)
	if ring2:
		ring2.rotate_y(-spin_base * 1.1 * delta)
	if shell:
		shell.rotate_y(spin_base * 0.5 * delta)

	var bob := sin(time_accum * 0.9) * pulse_amp * 0.2
	position.y = bob


func _update_mouse_push() -> void:
	if cam == null:
		mouse_push = 0.0
		return
	var screen_pos: Vector2 = cam.unproject_position(global_transform.origin)
	var mouse_pos: Vector2 = get_viewport().get_mouse_position()
	var dist: float = mouse_pos.distance_to(screen_pos)
	mouse_push = clamp(1.0 - dist / 480.0, 0.0, 1.0)


func _update_materials() -> void:
	var color := _mood_color()
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var spin_mod := preset["spin"]

	if core:
		var mat := core.material_override
		if mat is ShaderMaterial:
			mat.set_shader_parameter("core_color", color)
			mat.set_shader_parameter("edge_color", Color(1, 1, 1, 0.9))
			mat.set_shader_parameter("intensity", 0.25 + current_intensity * 0.5 + mouse_push * 0.2)
			mat.set_shader_parameter("pulse", 0.1 + current_intensity * 0.2)

	if ring:
		var rmat := ring.material_override
		if rmat is ShaderMaterial:
			rmat.set_shader_parameter("ring_color", color)
			rmat.set_shader_parameter("intensity", 0.2 + current_intensity * 0.4)
			rmat.set_shader_parameter("scroll_speed", 0.2 + spin_mod * 0.6)

	if ring2:
		var r2mat := ring2.material_override
		if r2mat is ShaderMaterial:
			var warm_mix := color.lerp(Color(1.0, 0.8, 0.5, 1.0), 0.3)
			r2mat.set_shader_parameter("ring_color", warm_mix)
			r2mat.set_shader_parameter("intensity", 0.15 + current_intensity * 0.3)
			r2mat.set_shader_parameter("scroll_speed", -0.15 - spin_mod * 0.5)
			r2mat.set_shader_parameter("line_density", 20.0 + current_intensity * 6.0)

	if shell:
		var smat := shell.material_override
		if smat is ShaderMaterial:
			smat.set_shader_parameter("energy_color", color)
			smat.set_shader_parameter("intensity", 0.15 + current_intensity * 0.25)
			smat.set_shader_parameter("grid_scale", 10.0 + current_intensity * 6.0)
			smat.set_shader_parameter("grid_thickness", 0.01 + mouse_push * 0.01)
			smat.set_shader_parameter("scan_speed", 0.2 + spin_mod * 0.4)


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
