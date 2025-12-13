shader_type spatial;
render_mode unshaded, cull_disabled, depth_prepass_alpha, blend_add;

uniform vec4 energy_color : source_color = vec4(0.35, 0.80, 1.00, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.5;
uniform float turbulence : hint_range(0.0, 2.0) = 0.35;
uniform float pulse : hint_range(0.0, 2.0) = 0.2;
uniform float time_scale : hint_range(0.1, 3.0) = 1.0;
uniform float mouse_push : hint_range(0.0, 1.0) = 0.0;
uniform float fresnel_power : hint_range(1.0, 8.0) = 3.0;

// Lightweight noise helpers (pseudo-fbm).
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

float fbm(vec3 p) {
	float f = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		f += a * noise(p);
		p *= 2.03;
		a *= 0.52;
	}
	return f;
}

void fragment() {
	float t = TIME * time_scale;
	vec3 nrm = normalize(NORMAL);
	vec3 view_dir = normalize(-VERTEX);

	// Multi-layer noise for swirling plasma.
	vec3 p = VERTEX * (2.4 + mouse_push * 0.5) + nrm * 0.6;
	float swirl = fbm(p + vec3(t * 0.7, t * 0.4, t * 0.9)) * turbulence;
	float swirl2 = fbm(p * 1.7 + vec3(-t * 0.3, t * 0.2, t * 0.5)) * (turbulence * 0.6);
	float wobble = swirl + swirl2;

	float r = length(VERTEX);
	float core = smoothstep(0.58 + wobble * 0.4, 0.08, r);
	float halo = smoothstep(0.35, 1.05 + wobble * 0.6, r + mouse_push * 0.12);

	float fres = pow(1.0 - max(dot(nrm, view_dir), 0.0), fresnel_power);
	float pulse_mod = 0.4 + 0.6 * sin(t * 2.1) * pulse;
	float spark = smoothstep(0.1, 0.9, fbm(p * 4.2 + vec3(t * 1.4))) * 0.8;

	vec3 col = energy_color.rgb;
	vec3 aura = mix(col, vec3(1.0, 0.9, 0.8), clamp(mouse_push * 0.5, 0.0, 1.0));
	float emit = intensity * 1.4 + core * 2.0 + halo * 1.0 + fres * 1.0 + pulse_mod * 0.6 + spark * 0.6;

	ALBEDO = col;
	EMISSION = aura * emit;
	ALPHA = clamp(core * 0.6 + halo * 0.5 + fres * 0.3, 0.03, 0.8);
}
