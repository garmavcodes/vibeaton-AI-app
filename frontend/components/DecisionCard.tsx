import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../lib/colors';

interface Props {
  decision: {
    decision_id: string;
    agent_type: string;
    decision_type: string;
    summary: string;
    reasoning: string;
    reasoning_steps: string[];
    outcome: string;
    confidence: number;
    execution_status: string;
    created_at: string;
  };
}

export default function DecisionCard({ decision }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isInventory = decision.agent_type === 'inventory';
  const agentColor = isInventory ? COLORS.inventoryAgent : COLORS.dispatchAgent;
  const agentIcon = isInventory ? 'cube' : 'car';
  const agentLabel = isInventory ? 'INVENTORY' : 'DISPATCH';

  const time = new Date(decision.created_at).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <TouchableOpacity
      testID={`decision-card-${decision.decision_id}`}
      style={[styles.card, { borderLeftColor: agentColor }]}
      onPress={() => setExpanded(!expanded)}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={[styles.badge, { backgroundColor: agentColor + '20' }]}>
          <Ionicons name={agentIcon as any} size={14} color={agentColor} />
          <Text style={[styles.badgeText, { color: agentColor }]}>{agentLabel}</Text>
        </View>
        <Text style={styles.time}>{time}</Text>
      </View>

      <Text style={styles.summary}>{decision.summary}</Text>

      <View style={styles.metaRow}>
        <View style={styles.confidenceBar}>
          <View style={[styles.confidenceFill, { width: `${decision.confidence * 100}%`, backgroundColor: agentColor }]} />
        </View>
        <Text style={styles.confidenceText}>{Math.round(decision.confidence * 100)}%</Text>
        <Ionicons
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={COLORS.textMuted}
        />
      </View>

      {expanded && (
        <View style={styles.details}>
          <Text style={styles.detailLabel}>REASONING STEPS</Text>
          {decision.reasoning_steps.map((step, i) => (
            <View key={i} style={styles.stepRow}>
              <Text style={[styles.stepNum, { color: agentColor }]}>{i + 1}</Text>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}

          {decision.reasoning ? (
            <>
              <Text style={[styles.detailLabel, { marginTop: 12 }]}>DETAILED ANALYSIS</Text>
              <Text style={styles.reasoning}>{decision.reasoning}</Text>
            </>
          ) : null}

          <View style={styles.outcomeBox}>
            <Ionicons name="checkmark-circle" size={14} color={COLORS.success} />
            <Text style={styles.outcomeText}>{decision.outcome}</Text>
          </View>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderLeftWidth: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  time: {
    fontSize: 11,
    color: COLORS.textMuted,
    fontVariant: ['tabular-nums'],
  },
  summary: {
    fontSize: 13,
    color: COLORS.textPrimary,
    lineHeight: 18,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  confidenceBar: {
    flex: 1,
    height: 3,
    backgroundColor: COLORS.border,
    borderRadius: 2,
  },
  confidenceFill: {
    height: 3,
    borderRadius: 2,
  },
  confidenceText: {
    fontSize: 10,
    color: COLORS.textMuted,
    fontWeight: '700',
  },
  details: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  detailLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  stepRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 6,
  },
  stepNum: {
    fontSize: 12,
    fontWeight: '900',
    width: 16,
  },
  stepText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 17,
  },
  reasoning: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  outcomeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
    backgroundColor: COLORS.success + '10',
    padding: 8,
    borderRadius: 8,
  },
  outcomeText: {
    fontSize: 12,
    color: COLORS.success,
    fontWeight: '600',
    flex: 1,
  },
});
