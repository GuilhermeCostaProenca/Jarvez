shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_add;

uniform vec4 base_color : source_color = vec4(0.25, 0.70, 1.00, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.6;
uniform float distortion : hint_range(0.0, 1.0) = 0.2;
uniform float noise_scale : hint_range(0.5, 3.0) = 1.6;
uniform float time_scale : hint_range(0.1, 3.0) = 1.0;
uniform float mouse_push : hint_range(0.0, 1.0) = 0.0;

float hash(vec3 p) {
	return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453);
}

float noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash(i + vec3(0, 0, 0)), hash(i + vec3(1, 0, 0)), u.x),
			mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), u.x), u.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), u.x),
			mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), u.x), u.y),
		u.z);
}

void vertex() {
	float t = TIME * time_scale;
	vec3 p = (NORMAL + VERTEX) * noise_scale;
	float n = noise(p + vec3(t * 0.8, t * 0.4, t * 1.1));
	float wobble = (n - 0.5) * distortion * 0.6 + mouse_push * 0.12;
	VERTEX += NORMAL * wobble;
}

void fragment() {
	float rim = clamp(abs(NORMAL.z), 0.0, 1.0);
	float glow = pow(rim, 6.0) + intensity * 0.5;
	float t = TIME * time_scale;
	float flicker = 0.25 + 0.25 * sin(t * 3.1);
	vec3 col = base_color.rgb;
	ALBEDO = col;
	EMISSION = col * (glow + flicker + mouse_push * 0.6);
	ALPHA = clamp(glow, 0.05, 1.0);
}
