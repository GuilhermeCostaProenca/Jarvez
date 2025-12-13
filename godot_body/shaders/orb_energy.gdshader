shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_alpha_prepass, blend_add;

uniform vec4 energy_color : source_color = vec4(0.35, 0.80, 1.00, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.5;
uniform float turbulence : hint_range(0.0, 2.0) = 0.35;
uniform float pulse : hint_range(0.0, 2.0) = 0.2;
uniform float time_scale : hint_range(0.1, 3.0) = 1.0;
uniform float mouse_push : hint_range(0.0, 1.0) = 0.0;

// Lightweight noise helpers (pseudo-fbm).
float hash(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	// Smooth interpolation
	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash(i + vec3(0.0, 0.0, 0.0)), hash(i + vec3(1.0, 0.0, 0.0)), u.x),
			mix(hash(i + vec3(0.0, 1.0, 0.0)), hash(i + vec3(1.0, 1.0, 0.0)), u.x), u.y),
		mix(mix(hash(i + vec3(0.0, 0.0, 1.0)), hash(i + vec3(1.0, 0.0, 1.0)), u.x),
			mix(hash(i + vec3(0.0, 1.0, 1.0)), hash(i + vec3(1.0, 1.0, 1.0)), u.x), u.y),
		u.z);
}

float fbm(vec3 p) {
	float f = 0.0;
	float a = 0.5;
	for (int i = 0; i < 4; i++) {
		f += a * noise(p);
		p *= 2.02;
		a *= 0.55;
	}
	return f;
}

void fragment() {
	float t = TIME * time_scale;
	// Position seed blends normal and vertex for an inner wobble.
	vec3 p = NORMAL * 0.4 + VERTEX * 0.8;
	float wobble = fbm(p * 3.2 + vec3(t * 0.6, t * 0.4, t * 0.7)) * turbulence;
	float push = mouse_push * 0.35 * sin(t * 2.3);

	float r = length(VERTEX);
	float core = smoothstep(0.6 + wobble, 0.1, r - push);
	float halo = smoothstep(0.4, 1.1 + wobble + push, r);
	float pulse_mod = 0.3 + 0.7 * sin(t * 2.2) * pulse;

	vec3 col = energy_color.rgb;
	float emit = intensity * 2.0 + core * 3.0 + halo * 1.4 + pulse_mod;

	ALBEDO = col;
	EMISSION = col * emit;
	ALPHA = clamp(core + halo * 0.7, 0.05, 1.0);
}
