import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, ActivityIndicator,
} from 'react-native';
import { apiCall } from '../../lib/api';
import { COLORS, stressColor } from '../../lib/colors';
import ChaosGauge from '../../components/ChaosGauge';
import MetricCard from '../../components/MetricCard';

export default function ChaosScreen() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await apiCall('/dashboard/metrics');
      setMetrics(data);
    } catch (e) {
      console.log('Metrics error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 4000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  if (loading || !metrics) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  const sc = stressColor(metrics.stress_level);

  return (
    <ScrollView
      testID="chaos-meter-screen"
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => { setRefreshing(true); fetchMetrics(); }}
          tintColor={COLORS.primary}
        />
      }
    >
      {/* Section Label */}
      <Text style={styles.sectionLabel}>SYSTEM STRESS LEVEL</Text>

      {/* Chaos Gauge */}
      <View style={styles.gaugeWrap}>
        <ChaosGauge level={metrics.stress_level} size={220} />
      </View>

      {/* Stress Test Indicator */}
      {metrics.stress_test_running && (
        <View style={styles.testBanner}>
          <View style={styles.pulsingDot} />
          <Text style={styles.testBannerText}>STRESS TEST IN PROGRESS</Text>
        </View>
      )}

      {/* Metrics Grid */}
      <Text style={[styles.sectionLabel, { marginTop: 24 }]}>OPERATIONAL METRICS</Text>

      <View style={styles.metricsGrid}>
        <MetricCard
          title="Active Orders"
          value={metrics.active_orders}
          icon="flame"
          color={metrics.active_orders > 30 ? COLORS.danger : COLORS.warning}
          subtitle={`${metrics.pending_orders} pending`}
        />
        <MetricCard
          title="Success Rate"
          value={`${metrics.success_rate}%`}
          icon="checkmark-circle"
          color={metrics.success_rate > 90 ? COLORS.success : COLORS.warning}
          subtitle={`${metrics.delivered} delivered`}
        />
      </View>

      <View style={styles.metricsGrid}>
        <MetricCard
          title="Avg Delivery"
          value={`${metrics.avg_delivery_time}m`}
          icon="timer"
          color={metrics.avg_delivery_time < 10 ? COLORS.success : COLORS.danger}
          subtitle="target: 10 min"
        />
        <MetricCard
          title="Inventory Health"
          value={`${metrics.inventory_health}%`}
          icon="cube"
          color={metrics.inventory_health > 60 ? COLORS.success : COLORS.warning}
        />
      </View>

      <View style={styles.metricsGrid}>
        <MetricCard
          title="Total Orders"
          value={metrics.total_orders}
          icon="receipt"
          color={COLORS.primary}
          subtitle={`${metrics.failed} failed`}
        />
        <MetricCard
          title="Agent Decisions"
          value={metrics.agent_decisions}
          icon="bulb"
          color={COLORS.inventoryAgent}
          subtitle={`${metrics.purchase_orders} POs`}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  center: {
    flex: 1,
    backgroundColor: COLORS.bg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: 16,
    paddingBottom: 30,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 2,
    marginBottom: 16,
  },
  gaugeWrap: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  testBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.danger + '15',
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.danger + '40',
    marginTop: 12,
  },
  pulsingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.danger,
  },
  testBannerText: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.danger,
    letterSpacing: 1.5,
  },
  metricsGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
  },
});
