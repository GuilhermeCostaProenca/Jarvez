extends Node3D

@export var core_mesh_path: NodePath
@export var ring_mesh_path: NodePath
@export var particles_path: NodePath
@export var camera_path: NodePath
@export var debug_label_path: NodePath

@onready var core: MeshInstance3D = get_node_or_null(core_mesh_path)
@onready var ring: MeshInstance3D = get_node_or_null(ring_mesh_path)
@onready var particles: GPUParticles3D = get_node_or_null(particles_path)
@onready var cam: Camera3D = get_node_or_null(camera_path)
@onready var debug_label: Label = get_node_or_null(debug_label_path)
@onready var state_bus: Node = $StateBus

var current_state := "idle"
var current_intensity := 0.5
var current_mood := "calm"

var drag_active := false
var last_mouse_pos := Vector2.ZERO
var rot_velocity := Vector2.ZERO
var mouse_push := 0.0
var time_accum := 0.0

const STATE_PRESETS := {
	"idle":       {"intensity": 0.40, "speed": 0.6, "glow": 0.5, "noise": 0.30, "pulse": 0.18, "deform": 0.10},
	"listening":  {"intensity": 0.55, "speed": 0.9, "glow": 0.8, "noise": 0.40, "pulse": 0.24, "deform": 0.14},
	"thinking":   {"intensity": 0.70, "speed": 1.1, "glow": 1.0, "noise": 0.55, "pulse": 0.32, "deform": 0.20},
	"speaking":   {"intensity": 0.85, "speed": 1.3, "glow": 1.2, "noise": 0.65, "pulse": 0.38, "deform": 0.24},
	"intense":    {"intensity": 1.00, "speed": 1.6, "glow": 1.4, "noise": 0.80, "pulse": 0.46, "deform": 0.32},
}


func _ready() -> void:
	if state_bus:
		state_bus.connect("state_changed", Callable(self, "_on_state_changed"))
		state_bus.connect("intensity_changed", Callable(self, "_on_intensity_changed"))
		state_bus.connect("mood_changed", Callable(self, "_on_mood_changed"))
	# Ensure an initial draw.
	_apply_state(true)


func _process(delta: float) -> void:
	time_accum += delta
	_update_mouse_push(delta)
	_update_rotation(delta)
	_update_materials(delta)
	_update_particles(delta)
	_update_debug()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			drag_active = mb.pressed
			last_mouse_pos = mb.position
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_nudge_intensity(0.05)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_nudge_intensity(-0.05)
	elif event is InputEventMouseMotion and drag_active:
		var mm := event as InputEventMouseMotion
		rot_velocity = mm.relative * 0.01
		last_mouse_pos = mm.position


func _nudge_intensity(amount: float) -> void:
	current_intensity = clamp(current_intensity + amount, 0.0, 1.2)
	_apply_state()


func _on_state_changed(new_state: String) -> void:
	current_state = new_state
	_apply_state()


func _on_intensity_changed(value: float) -> void:
	current_intensity = clamp(value, 0.0, 1.2)
	_apply_state()


func _on_mood_changed(value: String) -> void:
	current_mood = value
	_apply_state()


func _update_rotation(delta: float) -> void:
	if drag_active:
		rotation.x += rot_velocity.y * delta
		rotation.y += rot_velocity.x * delta
	# slow down over time
	rot_velocity = rot_velocity.lerp(Vector2.ZERO, clamp(4.0 * delta, 0.0, 1.0))


func _update_mouse_push(_delta: float) -> void:
	if cam == null:
		return
	var viewport_size: Vector2 = get_viewport().get_visible_rect().size
	var screen_pos: Vector2 = cam.project_position(global_transform.origin, viewport_size)
	var mouse_pos: Vector2 = get_viewport().get_mouse_position()
	var dist: float = mouse_pos.distance_to(screen_pos)
	# Closer mouse increases field distortion; clamp to a sensible radius.
	mouse_push = clamp(1.0 - (dist / 420.0), 0.0, 1.0)


func _update_materials(_delta: float) -> void:
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var target_intensity: float = lerp(preset["intensity"], current_intensity, 0.6)

	if core:
		var core_mat := core.material_override
		if core_mat is ShaderMaterial:
			core_mat.set_shader_parameter("intensity", target_intensity)
			core_mat.set_shader_parameter("turbulence", preset["noise"] + mouse_push * 0.3)
			core_mat.set_shader_parameter("pulse", preset["pulse"])
			core_mat.set_shader_parameter("time_scale", preset["speed"])
			core_mat.set_shader_parameter("mouse_push", mouse_push)
			core_mat.set_shader_parameter("energy_color", _mood_color())

	if ring:
		var ring_mat := ring.material_override
		if ring_mat is ShaderMaterial:
			ring_mat.set_shader_parameter("intensity", target_intensity * 0.9)
			ring_mat.set_shader_parameter("distortion", preset["deform"] + mouse_push * 0.25)
			ring_mat.set_shader_parameter("time_scale", preset["speed"])
			ring_mat.set_shader_parameter("mouse_push", mouse_push)
			ring_mat.set_shader_parameter("base_color", _mood_color())


func _update_particles(_delta: float) -> void:
	if particles == null:
		return
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	particles.speed_scale = preset["speed"]
	particles.amount = int(500 + 500 * current_intensity)
	particles.scale_amount_min = 0.7 + current_intensity * 0.2
	particles.scale_amount_max = 1.2 + current_intensity * 0.4


func _update_debug() -> void:
	if debug_label:
		debug_label.text = "state: %s | intensity: %.2f" % [current_state, current_intensity]


func _apply_state(_immediate: bool = false) -> void:
	# Called on state/intensity/mood changes; pushes parameters to materials immediately.
	_update_materials(0.0)
	_update_particles(0.0)
	_update_debug()


func _mood_color() -> Color:
	match current_mood:
		"calm":
			return Color(0.35, 0.80, 1.00, 1.0)
		"focus":
			return Color(0.40, 1.00, 0.80, 1.0)
		"warm":
			return Color(1.00, 0.65, 0.40, 1.0)
		"alert":
			return Color(1.00, 0.40, 0.50, 1.0)
		_:
			return Color(0.50, 0.80, 1.00, 1.0)
