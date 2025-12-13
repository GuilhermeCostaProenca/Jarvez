extends Node
class_name StateBus

signal state_changed(state: String)
signal intensity_changed(intensity: float)
signal mood_changed(mood: String)

const WS_URL := "ws://127.0.0.1:8787"
const RETRY_SEC := 2.5

var state: String = "idle"
var intensity: float = 0.5
var mood: String = "calm"

var _ws: WebSocketPeer = WebSocketPeer.new()
var _retry_timer: float = 0.0
var _connected: bool = false


func _ready() -> void:
	# Fire initial signals so listeners render something even before the socket connects.
	emit_signal("state_changed", state)
	emit_signal("intensity_changed", intensity)
	emit_signal("mood_changed", mood)
	_connect_ws()


func _process(delta: float) -> void:
	# Keep the socket alive and read incoming packets.
	var ws_state: int = _ws.get_ready_state()
	if ws_state == WebSocketPeer.STATE_CONNECTING or ws_state == WebSocketPeer.STATE_OPEN:
		_connected = ws_state == WebSocketPeer.STATE_OPEN
		_ws.poll()
		while _ws.get_available_packet_count() > 0:
			_handle_packet(_ws.get_packet())
	else:
		_connected = false
		_retry_timer -= delta
		if _retry_timer <= 0.0:
			_connect_ws()


func _connect_ws() -> void:
	_ws = WebSocketPeer.new()
	var err: int = _ws.connect_to_url(WS_URL)
	if err != OK:
		# If the server is down, schedule another try.
		_retry_timer = RETRY_SEC
	else:
		_retry_timer = RETRY_SEC


func _handle_packet(packet: PackedByteArray) -> void:
	var text := packet.get_string_from_utf8()
	var data = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		return
	_apply_payload(data)


func _apply_payload(data: Dictionary) -> void:
	if data.has("state"):
		var new_state: String = str(data["state"]).to_lower()
		if new_state != state:
			state = new_state
			emit_signal("state_changed", state)
	if data.has("intensity"):
		var new_intensity: float = clamp(float(data["intensity"]), 0.0, 1.2)
		if !is_equal_approx(new_intensity, intensity):
			intensity = new_intensity
			emit_signal("intensity_changed", intensity)
	if data.has("mood"):
		var new_mood: String = str(data["mood"]).to_lower()
		if new_mood != mood:
			mood = new_mood
			emit_signal("mood_changed", mood)


func ws_is_connected() -> bool:
	return _connected
