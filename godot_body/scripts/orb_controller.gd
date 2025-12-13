extends Node3D

@export var core_mesh_path: NodePath
@export var ring_mesh_path: NodePath
@export var ring2_mesh_path: NodePath
@export var particles_path: NodePath
@export var wisps_path: NodePath
@export var arcs_path: NodePath
@export var shell_mesh_path: NodePath
@export var camera_path: NodePath
@export var debug_label_path: NodePath

@onready var core: MeshInstance3D = get_node_or_null(core_mesh_path)
@onready var ring: MeshInstance3D = get_node_or_null(ring_mesh_path)
@onready var ring2: MeshInstance3D = get_node_or_null(ring2_mesh_path)
@onready var particles: GPUParticles3D = get_node_or_null(particles_path)
@onready var wisps: GPUParticles3D = get_node_or_null(wisps_path)
@onready var arcs: GPUParticles3D = get_node_or_null(arcs_path)
@onready var shell: MeshInstance3D = get_node_or_null(shell_mesh_path)
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

const MOOD_COLORS := {
	"calm": Color(0.35, 0.80, 1.00, 1.0),
	"focus": Color(0.35, 1.00, 0.90, 1.0),
	"warm": Color(1.00, 0.72, 0.35, 1.0),
	"alert": Color(1.00, 0.45, 0.40, 1.0),
	"intense": Color(1.00, 0.35, 0.20, 1.0)
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
	_update_motion(delta)
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


func _update_motion(delta: float) -> void:
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	var spin: float = (preset["speed"] * 0.5) + (current_intensity * 0.25)
	var bob_amp: float = 0.12 + current_intensity * 0.18
	var bob := sin(time_accum * (1.2 + current_intensity * 0.6) + mouse_push * 1.4) * bob_amp
	position.y = bob
	rotation.y += spin * delta * 0.35
	if ring:
		ring.rotate_y(spin * delta * 0.7)
	if ring2:
		ring2.rotate_y(-spin * delta * 0.6)
	if shell:
		shell.rotate_y(spin * delta * 0.2)


func _update_mouse_push(_delta: float) -> void:
	if cam == null:
		return
	# Convert orb world position to screen space for proximity distortion.
	var screen_pos: Vector2 = cam.unproject_position(global_transform.origin)
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

	if ring2:
		var ring2_mat := ring2.material_override
		if ring2_mat is ShaderMaterial:
			ring2_mat.set_shader_parameter("intensity", target_intensity * 0.7)
			ring2_mat.set_shader_parameter("distortion", preset["deform"] * 1.2 + mouse_push * 0.3)
			ring2_mat.set_shader_parameter("time_scale", preset["speed"] * 0.8)
			ring2_mat.set_shader_parameter("mouse_push", mouse_push)
			ring2_mat.set_shader_parameter("base_color", _mood_color().lerp(Color(1.0, 0.9, 0.7, 0.6), 0.2))

	if shell:
		var shell_mat := shell.material_override
		if shell_mat is ShaderMaterial:
			shell_mat.set_shader_parameter("intensity", target_intensity * 0.8 + mouse_push * 0.4)
			shell_mat.set_shader_parameter("noise_amp", preset["noise"] + mouse_push * 0.4)
			shell_mat.set_shader_parameter("time_scale", preset["speed"] * 0.9)
			shell_mat.set_shader_parameter("band_thickness", 0.32 + current_intensity * 0.18)
			shell_mat.set_shader_parameter("energy_color", _mood_color())


func _update_particles(_delta: float) -> void:
	var preset: Dictionary = STATE_PRESETS.get(current_state, STATE_PRESETS["idle"])
	if particles:
		particles.speed_scale = preset["speed"] * 0.9
		particles.amount = int(320 + 320 * current_intensity)
		var pm := particles.process_material
		if pm is ParticleProcessMaterial:
			pm.scale_min = 0.7 + current_intensity * 0.2
			pm.scale_max = 1.2 + current_intensity * 0.4
			var c := _mood_color()
			c.a = 0.75
			pm.color = c
	if wisps:
		wisps.speed_scale = preset["speed"] * 0.8
		wisps.amount = int(140 + 180 * current_intensity)
		var pm2 := wisps.process_material
		if pm2 is ParticleProcessMaterial:
			pm2.scale_min = 0.18 + current_intensity * 0.08
			pm2.scale_max = 0.32 + current_intensity * 0.1
			pm2.orbit_velocity_max = 1.2 + current_intensity * 0.6
			pm2.initial_velocity_min = 0.35 + current_intensity * 0.05
			pm2.initial_velocity_max = 0.9 + current_intensity * 0.15
			var c2 := _mood_color()
			c2.a = 0.65
			pm2.color = c2
	if arcs:
		arcs.speed_scale = preset["speed"] * 1.1
		arcs.amount = int(45 + 60 * current_intensity)
		var pm3 := arcs.process_material
		if pm3 is ParticleProcessMaterial:
			pm3.initial_velocity_min = 1.5 + current_intensity * 0.4
			pm3.initial_velocity_max = 2.8 + current_intensity * 0.8
			pm3.scale_min = 0.4 + current_intensity * 0.2
			pm3.scale_max = 0.8 + current_intensity * 0.35
			var c3 := _mood_color()
			c3.a = 0.8
			pm3.color = c3


func _update_debug() -> void:
	if debug_label:
		var ws_ok := false
		if state_bus and state_bus.has_method("ws_is_connected"):
			ws_ok = state_bus.call("ws_is_connected")
		var ws_label := "ok" if ws_ok else "down"
		debug_label.text = "state: %s | intensity: %.2f | ws: %s" % [current_state, current_intensity, ws_label]


func _apply_state(_immediate: bool = false) -> void:
	# Called on state/intensity/mood changes; pushes parameters to materials immediately.
	_update_materials(0.0)
	_update_particles(0.0)
	_update_debug()


func _mood_color() -> Color:
	if MOOD_COLORS.has(current_mood):
		return MOOD_COLORS[current_mood]
	return MOOD_COLORS["calm"]
