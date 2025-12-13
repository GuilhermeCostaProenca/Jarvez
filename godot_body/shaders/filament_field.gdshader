shader_type spatial;
render_mode unshaded, cull_disabled, depth_prepass_alpha, blend_add;

uniform vec4 energy_color : source_color = vec4(0.35, 0.8, 1.0, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.6;
uniform float noise_scale : hint_range(0.5, 4.0) = 2.2;
uniform float time_scale : hint_range(0.1, 3.0) = 1.1;
uniform float band_thickness : hint_range(0.05, 0.8) = 0.35;
uniform float noise_amp : hint_range(0.0, 2.0) = 0.5;
uniform float pulse : hint_range(0.0, 2.0) = 0.4;
uniform float mouse_push : hint_range(0.0, 1.0) = 0.0;

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

float ridge_noise(vec3 p) {
	float n = noise(p);
	return 1.0 - abs(n * 2.0 - 1.0);
}

void fragment() {
	float t = TIME * time_scale;
	vec3 p = normalize(VERTEX) * noise_scale;
	float ridges = ridge_noise(p + vec3(t * 0.6, t * 0.3, -t * 0.7));
	float ridges2 = ridge_noise(p * 1.9 + vec3(-t * 0.4, t * 0.5, t * 0.2));
	float filaments = pow(ridges, 4.0) + pow(ridges2, 3.0);

	// Banding effect
	float band = abs(sin(dot(normalize(VERTEX), vec3(1.2, 0.8, 0.6)) * 6.0 + t * 1.6));
	float band_mask = smoothstep(band_thickness, band_thickness - 0.2, band);

	float pulse_mod = 0.4 + 0.6 * sin(t * 2.0) * pulse;
	float push = mouse_push * 0.8;

	vec3 col = energy_color.rgb;
	float emit = intensity * 0.6 + filaments * (1.8 + push) + band_mask * 1.4 + pulse_mod;

	ALBEDO = col;
	EMISSION = col * emit;
	ALPHA = clamp(filaments + band_mask * 0.6, 0.05, 0.9);
}
