import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path, Circle, G } from 'react-native-svg';
import { COLORS, stressColor } from '../lib/colors';

interface Props {
  level: number;
  size?: number;
}

export default function ChaosGauge({ level, size = 200 }: Props) {
  const r = (size - 20) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const startAngle = 135;
  const endAngle = 405;
  const totalAngle = endAngle - startAngle;
  const clampedLevel = Math.max(0, Math.min(100, level));
  const sweepAngle = (clampedLevel / 100) * totalAngle;

  function polarToCartesian(angle: number) {
    const rad = ((angle - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function describeArc(start: number, end: number) {
    const s = polarToCartesian(start);
    const e = polarToCartesian(end);
    const largeArc = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${largeArc} 1 ${e.x} ${e.y}`;
  }

  const bgPath = describeArc(startAngle, endAngle);
  const valuePath = sweepAngle > 0.5 ? describeArc(startAngle, startAngle + sweepAngle) : '';
  const color = stressColor(clampedLevel);
  const statusText = clampedLevel < 40 ? 'NOMINAL' : clampedLevel < 70 ? 'ELEVATED' : 'CRITICAL';

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size}>
        <Path d={bgPath} stroke={COLORS.border} strokeWidth={12} fill="none" strokeLinecap="round" />
        {valuePath ? (
          <Path d={valuePath} stroke={color} strokeWidth={12} fill="none" strokeLinecap="round" />
        ) : null}
        <Circle cx={cx} cy={cy} r={4} fill={color} />
      </Svg>
      <View style={styles.centerText}>
        <Text style={[styles.value, { color }]}>{Math.round(clampedLevel)}</Text>
        <Text style={styles.unit}>%</Text>
        <Text style={[styles.status, { color }]}>{statusText}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerText: {
    position: 'absolute',
    alignItems: 'center',
  },
  value: {
    fontSize: 48,
    fontWeight: '900',
    letterSpacing: -2,
  },
  unit: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: -4,
  },
  status: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 2,
    marginTop: 4,
  },
});
