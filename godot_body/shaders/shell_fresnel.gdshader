shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_add;

uniform vec4 energy_color : source_color = vec4(0.3, 0.85, 1.0, 1.0);
uniform float intensity : hint_range(0.0, 1.0) = 0.25;
uniform float fresnel_power : hint_range(1.0, 6.0) = 3.5;
uniform float grid_scale : hint_range(4.0, 32.0) = 14.0;
uniform float grid_thickness : hint_range(0.001, 0.05) = 0.015;
uniform float scan_speed : hint_range(0.0, 2.0) = 0.3;
uniform float wave_amp : hint_range(0.0, 0.2) = 0.02;

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

void vertex() {
	float t = TIME * scan_speed;
	float wave = sin((VERTEX.y + VERTEX.x * 0.4 + VERTEX.z * 0.3) * 2.5 + t) * wave_amp;
	VERTEX += NORMAL * wave;
}

void fragment() {
	float t = TIME * scan_speed;
	vec3 nrm = normalize(NORMAL);
	vec3 view_dir = normalize(-VERTEX);
	float fres = pow(1.0 - max(dot(nrm, view_dir), 0.0), fresnel_power);

	vec3 p = VERTEX * grid_scale;
	vec3 g = abs(fract(p + vec3(t, -t * 0.5, t * 0.3)) - 0.5);
	float line = min(g.x, min(g.y, g.z));
	float grid = smoothstep(grid_thickness, grid_thickness * 0.4, line);

	float jitter = noise(p * 1.2 + vec3(t * 0.5, -t * 0.3, t * 0.2)) * 0.3;

	vec3 col = energy_color.rgb;
	float emit = intensity + fres * 0.9 + grid * 1.1 + jitter * 0.5;

	ALBEDO = col;
	EMISSION = col * emit;
	ALPHA = clamp(fres * 0.6 + grid * 0.7, 0.05, 0.8);
}
