shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_add;

uniform vec4 ring_color : source_color = vec4(0.35, 0.9, 1.0, 1.0);
uniform float intensity : hint_range(0.0, 1.5) = 0.5;
uniform float line_density : hint_range(4.0, 48.0) = 16.0;
uniform float line_thickness : hint_range(0.001, 0.1) = 0.015;
uniform float scroll_speed : hint_range(-2.0, 2.0) = 0.3;
uniform float fresnel_power : hint_range(1.0, 6.0) = 3.0;

void vertex() {
	float t = TIME * scroll_speed;
	vec3 p = VERTEX * line_density;
	float band = abs(fract(p.x + t) - 0.5);
	float wobble = smoothstep(line_thickness * 2.0, line_thickness, band) * 0.04;
	VERTEX += NORMAL * wobble;
}

void fragment() {
	vec3 nrm = normalize(NORMAL);
	vec3 view_dir = normalize(-VERTEX);
	float fres = pow(1.0 - max(dot(nrm, view_dir), 0.0), fresnel_power);

	vec3 p = VERTEX * line_density;
	float line_x = abs(fract(p.x) - 0.5);
	float line_y = abs(fract(p.y) - 0.5);
	float line_z = abs(fract(p.z) - 0.5);
	float band = min(line_x, min(line_y, line_z));
	float stripes = smoothstep(line_thickness * 1.5, line_thickness, band);

	float emit = intensity * 0.8 + stripes * 1.2 + fres * 0.6;
	vec3 col = ring_color.rgb;

	ALBEDO = col;
	EMISSION = col * emit;
	ALPHA = clamp(stripes * 0.7 + fres * 0.5, 0.05, 0.85);
}
