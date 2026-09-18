# Temas CSS por rubro

Variables `:root` para inyectar según `HERMES_PROFILE`. No son marca de un cliente: cada local elige un tema dentro de su rubro.

El hub aplica el tema **por defecto** del perfil (`GET /api/instance` → `profile` → `html[data-theme]`). La alternativa (`HERMES_THEME`) queda para después.

| Perfil | Tema por defecto | Alternativa |
|---|---|---|
| `restaurant` | Fine Dining | Bistro Rústico |
| `bar` | Cyber Neon | Red Oak Wood |
| `buffet` | Fresh & Green | Comfort Warm |
| `qsr` | High-Contrast Pop | Midnight Street |
| `convenience` | Corporate Clean | Retro Arcade |

Variables comunes: `--hermes-bg-app`, `--hermes-bg-surface`, `--hermes-accent`, `--hermes-accent-hover`, `--hermes-text-main`, `--hermes-text-muted`, `--hermes-border`, `--hermes-radius`, `--hermes-touch-feedback`, `--hermes-late` (rojo de ticket atrasado en KDS).

## restaurant — Fine Dining

Uso: mantel, alta cocina, luz tenue. Tipografía: Roboto (no serif).

```css
:root {
  --hermes-bg-app: #0f1011;
  --hermes-bg-surface: #17191b;
  --hermes-accent: #c5a880;
  --hermes-accent-hover: #e2cfa8;
  --hermes-text-main: #f4f5f6;
  --hermes-text-muted: #8e9399;
  --hermes-border: #282b30;
  --hermes-radius: 4px;
  --hermes-touch-feedback: rgba(197, 168, 128, 0.15);
}
```

## restaurant — Bistro Rústico

Uso: café de especialidad, pizza artesanal, madera.

```css
:root {
  --hermes-bg-app: #fdfbf7;
  --hermes-bg-surface: #ffffff;
  --hermes-accent: #2e5a44;
  --hermes-accent-hover: #417a5e;
  --hermes-text-main: #2d2219;
  --hermes-text-muted: #7c6e64;
  --hermes-border: #eaddd3;
  --hermes-radius: 8px;
  --hermes-touch-feedback: rgba(46, 90, 68, 0.1);
}
```

## bar — Cyber Neon

Uso: gastrobar, coctelería, OLED.

```css
:root {
  --hermes-bg-app: #050508;
  --hermes-bg-surface: #0f111a;
  --hermes-accent: #00f0ff;
  --hermes-accent-hover: #70f8ff;
  --hermes-text-main: #ffffff;
  --hermes-text-muted: #6b7280;
  --hermes-border: #1e2235;
  --hermes-radius: 12px;
  --hermes-touch-feedback: rgba(0, 240, 255, 0.2);
}
```

## bar — Red Oak Wood

Uso: pub, sports bar, madera oscura.

```css
:root {
  --hermes-bg-app: #1c110e;
  --hermes-bg-surface: #2c1a16;
  --hermes-accent: #8b2617;
  --hermes-accent-hover: #d34935;
  --hermes-text-main: #f5ece9;
  --hermes-text-muted: #b59f9a;
  --hermes-border: #422923;
  --hermes-radius: 6px;
  --hermes-touch-feedback: rgba(139, 38, 23, 0.3);
}
```

## buffet — Fresh & Green

Uso: barra fría, vegetariano, diurno.

```css
:root {
  --hermes-bg-app: #f4f7f5;
  --hermes-bg-surface: #ffffff;
  --hermes-accent: #10b981;
  --hermes-accent-hover: #059669;
  --hermes-text-main: #0f172a;
  --hermes-text-muted: #64748b;
  --hermes-border: #e2e8f0;
  --hermes-radius: 16px;
  --hermes-touch-feedback: rgba(16, 185, 129, 0.1);
}
```

## buffet — Comfort Warm

Uso: buffet caliente, familiar.

```css
:root {
  --hermes-bg-app: #fbf7f0;
  --hermes-bg-surface: #ffffff;
  --hermes-accent: #d97706;
  --hermes-accent-hover: #b45309;
  --hermes-text-main: #451a03;
  --hermes-text-muted: #78350f;
  --hermes-border: #fed7aa;
  --hermes-radius: 10px;
  --hermes-touch-feedback: rgba(217, 119, 6, 0.15);
}
```

## qsr — High-Contrast Pop

Uso: fast food de volumen.

```css
:root {
  --hermes-bg-app: #ffffff;
  --hermes-bg-surface: #f8fafc;
  --hermes-accent: #ef4444;
  --hermes-accent-hover: #dc2626;
  --hermes-text-main: #0f172a;
  --hermes-text-muted: #475569;
  --hermes-border: #cbd5e1;
  --hermes-radius: 8px;
  --hermes-touch-feedback: rgba(239, 68, 68, 0.2);
}
```

## qsr — Midnight Street

Uso: food truck, taquería urbana.

```css
:root {
  --hermes-bg-app: #0b0f19;
  --hermes-bg-surface: #161b26;
  --hermes-accent: #eab308;
  --hermes-accent-hover: #ca8a04;
  --hermes-text-main: #f8fafc;
  --hermes-text-muted: #94a3b8;
  --hermes-border: #242b3d;
  --hermes-radius: 14px;
  --hermes-touch-feedback: rgba(234, 179, 8, 0.2);
}
```

## convenience — Corporate Clean

Uso: minimarket, gasolinera.

```css
:root {
  --hermes-bg-app: #f1f5f9;
  --hermes-bg-surface: #ffffff;
  --hermes-accent: #2563eb;
  --hermes-accent-hover: #1d4ed8;
  --hermes-text-main: #1e293b;
  --hermes-text-muted: #64748b;
  --hermes-border: #e2e8f0;
  --hermes-radius: 6px;
  --hermes-touch-feedback: rgba(37, 99, 235, 0.1);
}
```

## convenience — Retro Arcade

Uso: snacks, gaming, público joven.

```css
:root {
  --hermes-bg-app: #120e2e;
  --hermes-bg-surface: #1f1a4a;
  --hermes-accent: #ec4899;
  --hermes-accent-hover: #db2777;
  --hermes-text-main: #fdf2f8;
  --hermes-text-muted: #a21caf;
  --hermes-border: #3b2e7a;
  --hermes-radius: 2px;
  --hermes-touch-feedback: rgba(236, 72, 153, 0.3);
}
```

## Cómo está cableado

`GET /api/instance` trae `profile`. El frontend pone `data-theme="{profile}"` en `html` y los componentes usan `var(--hermes-*)`. No hay hex sueltos en botones ni tarjetas.

Tema por defecto del perfil primero; la alternativa se elige después con `HERMES_THEME` si hace falta.
