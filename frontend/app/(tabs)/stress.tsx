import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, ScrollView, StyleSheet, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiCall } from '../../lib/api';
import { COLORS, stressColor } from '../../lib/colors';

export default function StressScreen() {
  const [orderCount, setOrderCount] = useState(50);
  const [status, setStatus] = useState<any>(null);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiCall('/stress-test/status');
      setStatus(data);
      if (data.running) {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch {}
  }, []);

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    if (polling) {
      const interval = setInterval(fetchStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [polling, fetchStatus]);

  async function startTest() {
    setStarting(true);
    try {
      await apiCall('/stress-test/start', {
        method: 'POST',
        body: JSON.stringify({ order_count: orderCount }),
      });
      setPolling(true);
      fetchStatus();
    } catch (e: any) {
      console.log('Stress test error:', e);
    } finally {
      setStarting(false);
    }
  }

  const isRunning = status?.running;
  const results = status?.results;

  return (
    <ScrollView testID="stress-test-screen" style={styles.container} contentContainerStyle={styles.content}>
      {/* Title */}
      <View style={styles.titleSection}>
        <Ionicons name="flash" size={28} color={COLORS.danger} />
        <Text style={styles.title}>Stress Test Engine</Text>
        <Text style={styles.desc}>
          Simulate high-volume order floods to validate the backend's decision-making under pressure
        </Text>
      </View>

      {/* Config */}
      <View style={styles.configCard}>
        <Text style={styles.configLabel}>ORDER VOLUME</Text>
        <View style={styles.counterRow}>
          <TouchableOpacity
            testID="decrease-count-btn"
            style={styles.counterBtn}
            onPress={() => setOrderCount(Math.max(10, orderCount - 10))}
          >
            <Ionicons name="remove" size={20} color={COLORS.textPrimary} />
          </TouchableOpacity>
          <View style={styles.counterDisplay}>
            <Text style={styles.counterValue}>{orderCount}</Text>
            <Text style={styles.counterUnit}>orders</Text>
          </View>
          <TouchableOpacity
            testID="increase-count-btn"
            style={styles.counterBtn}
            onPress={() => setOrderCount(Math.min(200, orderCount + 10))}
          >
            <Ionicons name="add" size={20} color={COLORS.textPrimary} />
          </TouchableOpacity>
        </View>

        {/* Presets */}
        <View style={styles.presets}>
          {[50, 100, 150, 200].map(n => (
            <TouchableOpacity
              key={n}
              testID={`preset-${n}-btn`}
              style={[styles.presetBtn, orderCount === n && styles.presetBtnActive]}
              onPress={() => setOrderCount(n)}
            >
              <Text style={[styles.presetText, orderCount === n && styles.presetTextActive]}>{n}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Start Button */}
      <TouchableOpacity
        testID="start-stress-test-btn"
        style={[styles.startBtn, isRunning && styles.startBtnDisabled]}
        onPress={startTest}
        disabled={isRunning || starting}
        activeOpacity={0.7}
      >
        {starting ? (
          <ActivityIndicator color="#fff" />
        ) : isRunning ? (
          <>
            <ActivityIndicator color="#fff" size="small" />
            <Text style={styles.startBtnText}>Test Running...</Text>
          </>
        ) : (
          <>
            <Ionicons name="flash" size={22} color="#fff" />
            <Text style={styles.startBtnText}>LAUNCH STRESS TEST</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Progress */}
      {isRunning && (
        <View style={styles.progressCard}>
          <Text style={styles.progressLabel}>PROGRESS</Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${status.progress || 0}%` }]} />
          </View>
          <View style={styles.progressStats}>
            <ProgressStat label="Orders Created" value={status.orders_created || 0} />
            <ProgressStat label="Decisions Made" value={status.decisions_made || 0} />
            <ProgressStat label="Progress" value={`${status.progress || 0}%`} />
          </View>
        </View>
      )}

      {/* Results */}
      {results && !isRunning && !results.error && (
        <View style={styles.resultsCard}>
          <View style={styles.resultsHeader}>
            <Ionicons name="analytics" size={20} color={COLORS.success} />
            <Text style={styles.resultsTitle}>Test Results</Text>
          </View>

          <View style={styles.resultGrid}>
            <ResultItem label="Total Orders" value={results.total_orders} color={COLORS.primary} />
            <ResultItem label="Processed" value={results.orders_processed} color={COLORS.success} />
            <ResultItem label="Still Active" value={results.orders_still_active} color={COLORS.warning} />
            <ResultItem
              label="Success Rate"
              value={`${results.success_rate}%`}
              color={results.success_rate > 90 ? COLORS.success : COLORS.danger}
            />
            <ResultItem label="POs Generated" value={results.purchase_orders_generated} color={COLORS.inventoryAgent} />
            <ResultItem label="Agent Decisions" value={results.agent_decisions} color={COLORS.dispatchAgent} />
          </View>

          <View style={styles.durationRow}>
            <Ionicons name="time" size={14} color={COLORS.textMuted} />
            <Text style={styles.durationText}>
              Completed in {results.duration_seconds}s
            </Text>
          </View>
        </View>
      )}

      {/* Instructions */}
      {!isRunning && !results && (
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>What happens during a stress test?</Text>
          <InfoStep num="1" text="Generates simultaneous orders across all delivery zones" />
          <InfoStep num="2" text="Inventory Agent detects stockouts and auto-generates purchase orders" />
          <InfoStep num="3" text="Dispatch Agent batches orders and optimizes picking paths" />
          <InfoStep num="4" text="System tracks success rates, delivery times, and agent response quality" />
        </View>
      )}
    </ScrollView>
  );
}

function ProgressStat({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.pStatItem}>
      <Text style={styles.pStatValue}>{value}</Text>
      <Text style={styles.pStatLabel}>{label}</Text>
    </View>
  );
}

function ResultItem({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <View style={styles.resultItem}>
      <Text style={[styles.resultValue, { color }]}>{value}</Text>
      <Text style={styles.resultLabel}>{label}</Text>
    </View>
  );
}

function InfoStep({ num, text }: { num: string; text: string }) {
  return (
    <View style={styles.infoStep}>
      <View style={styles.infoNum}>
        <Text style={styles.infoNumText}>{num}</Text>
      </View>
      <Text style={styles.infoStepText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  titleSection: {
    alignItems: 'center',
    marginBottom: 24,
    gap: 6,
  },
  title: {
    fontSize: 22,
    fontWeight: '900',
    color: COLORS.textPrimary,
    letterSpacing: -0.5,
  },
  desc: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 12,
  },
  configCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 16,
  },
  configLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 16,
  },
  counterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 20,
  },
  counterBtn: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  counterDisplay: {
    alignItems: 'center',
  },
  counterValue: {
    fontSize: 48,
    fontWeight: '900',
    color: COLORS.danger,
    letterSpacing: -2,
  },
  counterUnit: {
    fontSize: 12,
    color: COLORS.textMuted,
    fontWeight: '600',
    marginTop: -4,
  },
  presets: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginTop: 16,
  },
  presetBtn: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  presetBtnActive: {
    backgroundColor: COLORS.danger + '15',
    borderColor: COLORS.danger + '50',
  },
  presetText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textMuted,
  },
  presetTextActive: {
    color: COLORS.danger,
  },
  startBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: COLORS.danger,
    borderRadius: 14,
    paddingVertical: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.danger,
  },
  startBtnDisabled: {
    backgroundColor: COLORS.danger + '60',
    borderColor: COLORS.danger + '40',
  },
  startBtnText: {
    fontSize: 16,
    fontWeight: '900',
    color: '#fff',
    letterSpacing: 1,
  },
  progressCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.danger + '40',
    marginBottom: 16,
  },
  progressLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 1.5,
    marginBottom: 10,
  },
  progressBar: {
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
    marginBottom: 16,
  },
  progressFill: {
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.danger,
  },
  progressStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  pStatItem: {
    alignItems: 'center',
  },
  pStatValue: {
    fontSize: 20,
    fontWeight: '900',
    color: COLORS.textPrimary,
  },
  pStatLabel: {
    fontSize: 10,
    color: COLORS.textMuted,
    fontWeight: '600',
    marginTop: 2,
  },
  resultsCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.success + '40',
    marginBottom: 16,
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  resultGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  resultItem: {
    width: '30%',
    alignItems: 'center',
  },
  resultValue: {
    fontSize: 22,
    fontWeight: '900',
  },
  resultLabel: {
    fontSize: 10,
    color: COLORS.textMuted,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 2,
  },
  durationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  durationText: {
    fontSize: 12,
    color: COLORS.textMuted,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 14,
  },
  infoStep: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
  },
  infoNum: {
    width: 24,
    height: 24,
    borderRadius: 6,
    backgroundColor: COLORS.primary + '15',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoNumText: {
    fontSize: 12,
    fontWeight: '900',
    color: COLORS.primary,
  },
  infoStepText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 18,
  },
});
