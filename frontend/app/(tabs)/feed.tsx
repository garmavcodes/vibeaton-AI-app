import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiCall } from '../../lib/api';
import { COLORS } from '../../lib/colors';
import DecisionCard from '../../components/DecisionCard';

export default function FeedScreen() {
  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  const fetchFeed = useCallback(async () => {
    try {
      const data = await apiCall('/dashboard/live-feed?limit=40');
      setDecisions(data);
    } catch (e) {
      console.log('Feed error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, 5000);
    return () => clearInterval(interval);
  }, [fetchFeed]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchFeed();
  };

  const filtered = filter === 'all' ? decisions : decisions.filter(d => d.agent_type === filter);

  const createOrder = async () => {
    try {
      await apiCall('/orders/create', { method: 'POST' });
      fetchFeed();
    } catch {}
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadText}>Loading agent decisions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Filter Bar */}
      <View style={styles.filterBar}>
        {[
          { key: 'all', label: 'All', icon: 'layers' },
          { key: 'inventory', label: 'Inventory', icon: 'cube' },
          { key: 'dispatch', label: 'Dispatch', icon: 'car' },
        ].map(f => (
          <TouchableOpacity
            key={f.key}
            testID={`filter-${f.key}-btn`}
            style={[styles.filterBtn, filter === f.key && styles.filterBtnActive]}
            onPress={() => setFilter(f.key)}
          >
            <Ionicons
              name={f.icon as any}
              size={14}
              color={filter === f.key ? COLORS.primary : COLORS.textMuted}
            />
            <Text style={[styles.filterText, filter === f.key && styles.filterTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
        <TouchableOpacity testID="create-order-btn" style={styles.addBtn} onPress={createOrder}>
          <Ionicons name="add" size={18} color={COLORS.textPrimary} />
        </TouchableOpacity>
      </View>

      {/* Decision Count */}
      <View style={styles.countRow}>
        <Ionicons name="pulse" size={14} color={COLORS.success} />
        <Text style={styles.countText}>
          {filtered.length} decisions • Auto-refreshing
        </Text>
      </View>

      {/* Feed List */}
      <FlatList
        testID="live-feed-list"
        data={filtered}
        keyExtractor={(item) => item.decision_id}
        renderItem={({ item }) => <DecisionCard decision={item} />}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="hourglass-outline" size={48} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>No agent decisions yet</Text>
            <Text style={styles.emptySubtext}>Agents are monitoring... decisions will appear here</Text>
            <TouchableOpacity testID="trigger-order-btn" style={styles.triggerBtn} onPress={createOrder}>
              <Text style={styles.triggerBtnText}>Create Test Order</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
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
  loadText: {
    color: COLORS.textMuted,
    marginTop: 12,
    fontSize: 13,
  },
  filterBar: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
    alignItems: 'center',
  },
  filterBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  filterBtnActive: {
    backgroundColor: COLORS.primary + '15',
    borderColor: COLORS.primary + '50',
  },
  filterText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  filterTextActive: {
    color: COLORS.primary,
  },
  addBtn: {
    marginLeft: 'auto',
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  countRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  countText: {
    fontSize: 11,
    color: COLORS.textMuted,
    fontWeight: '600',
  },
  listContent: {
    paddingHorizontal: 12,
    paddingBottom: 20,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 60,
    gap: 8,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textSecondary,
  },
  emptySubtext: {
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
  },
  triggerBtn: {
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  triggerBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 13,
  },
});
