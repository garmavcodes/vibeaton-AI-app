export const COLORS = {
  bg: '#0A0A0A',
  surface: '#121212',
  surfaceLight: '#1A1A1A',
  surfaceGlass: 'rgba(18, 18, 18, 0.9)',
  border: '#27272A',
  borderLight: '#3F3F46',
  primary: '#007AFF',
  danger: '#FF3B30',
  success: '#34C759',
  warning: '#FFCC00',
  orange: '#FF9500',
  textPrimary: '#FFFFFF',
  textSecondary: '#A1A1AA',
  textMuted: '#52525B',
  inventoryAgent: '#34C759',
  dispatchAgent: '#007AFF',
};

export function stockColor(status: string) {
  switch (status) {
    case 'critical': return COLORS.danger;
    case 'low': return COLORS.orange;
    case 'moderate': return COLORS.warning;
    case 'healthy': return COLORS.success;
    default: return COLORS.textMuted;
  }
}

export function stressColor(level: number) {
  if (level < 40) return COLORS.success;
  if (level < 70) return COLORS.warning;
  return COLORS.danger;
}
