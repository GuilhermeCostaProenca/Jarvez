shader_type spatial;
render_mode unshaded, cull_disabled, depth_prepass_alpha, blend_add;

uniform vec4 core_color : source_color = vec4(0.25, 0.80, 1.00, 1.0);
uniform vec4 edge_color : source_color = vec4(0.9, 1.0, 1.0, 0.8);
uniform float intensity : hint_range(0.0, 1.5) = 0.5;
uniform float fresnel_power : hint_range(1.0, 6.0) = 3.0;
uniform float grid_scale : hint_range(2.0, 24.0) = 10.0;
uniform float grid_thickness : hint_range(0.001, 0.1) = 0.02;
uniform float scan_speed : hint_range(0.0, 2.0) = 0.3;
uniform float pulse : hint_range(0.0, 1.0) = 0.25;

float hash(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash(i + vec3(0.0, 0.0, 0.0)), hash(i + vec3(1.0, 0.0, 0.0)), u.x),
			mix(hash(i + vec3(0.0, 1.0, 0.0)), hash(i + vec3(1.0, 1.0, 0.0)), u.x), u.y),
		mix(mix(hash(i + vec3(0.0, 0.0, 1.0)), hash(i + vec3(1.0, 0.0, 1.0)), u.x),
			mix(hash(i + vec3(0.0, 1.0, 1.0)), hash(i + vec3(1.0, 1.0, 1.0)), u.x), u.y),
		u.z);
}

float grid_layer(vec3 p) {
	p *= grid_scale;
	vec3 g = abs(fract(p) - 0.5);
	float line = min(g.x, min(g.y, g.z));
	return smoothstep(grid_thickness, grid_thickness * 0.5, line);
}

void fragment() {
	float t = TIME;
	vec3 nrm = normalize(NORMAL);
	vec3 view_dir = normalize(-VERTEX);
	float fres = pow(1.0 - max(dot(nrm, view_dir), 0.0), fresnel_power);

	vec3 p = VERTEX * 1.5;
	float scan = sin((p.y + p.x * 0.3) * 0.6 + t * scan_speed);
	float grid = grid_layer(p + vec3(0.0, t * scan_speed, 0.0));
	float jitter = noise(p * 2.2 + vec3(t * 0.2, -t * 0.15, t * 0.25)) * 0.3;

	float core = smoothstep(0.7, 0.1, length(VERTEX));
	float pulse_mod = 0.6 + 0.4 * sin(t * 2.0) * pulse;

	vec3 col = mix(core_color.rgb, edge_color.rgb, fres);
	float emit = intensity * 0.8 + core * 1.2 + fres * 0.9 + grid * 0.8 + scan * 0.15 + jitter * 0.4 + pulse_mod * 0.3;

	ALBEDO = col;
	EMISSION = col * emit;
	ALPHA = clamp(core * 0.6 + fres * 0.5 + grid * 0.3, 0.05, 0.85);
}
