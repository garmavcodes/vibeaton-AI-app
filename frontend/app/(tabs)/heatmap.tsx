import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiCall } from '../../lib/api';
import { COLORS, stockColor } from '../../lib/colors';

export default function HeatmapScreen() {
  const [products, setProducts] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCat, setSelectedCat] = useState('All');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [prods, cats] = await Promise.all([
        apiCall(`/dashboard/stock-heatmap?category=${selectedCat}`),
        apiCall('/dashboard/categories'),
      ]);
      setProducts(prods);
      setCategories(cats);
    } catch (e) {
      console.log('Heatmap error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedCat]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const stats = {
    critical: products.filter(p => p.status === 'critical').length,
    low: products.filter(p => p.status === 'low').length,
    moderate: products.filter(p => p.status === 'moderate').length,
    healthy: products.filter(p => p.status === 'healthy').length,
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Stats Summary */}
      <View style={styles.statsBar}>
        <StatPill label="Critical" count={stats.critical} color={COLORS.danger} />
        <StatPill label="Low" count={stats.low} color={COLORS.orange} />
        <StatPill label="Moderate" count={stats.moderate} color={COLORS.warning} />
        <StatPill label="Healthy" count={stats.healthy} color={COLORS.success} />
      </View>

      {/* Category Filter */}
      <FlatList
        horizontal
        data={categories}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.catList}
        renderItem={({ item }) => (
          <TouchableOpacity
            testID={`cat-filter-${item}`}
            style={[styles.catBtn, selectedCat === item && styles.catBtnActive]}
            onPress={() => setSelectedCat(item)}
          >
            <Text style={[styles.catText, selectedCat === item && styles.catTextActive]}>
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Product Grid */}
      <FlatList
        testID="stock-heatmap-grid"
        data={products}
        numColumns={2}
        keyExtractor={(item) => item.product_id}
        contentContainerStyle={styles.gridContent}
        columnWrapperStyle={styles.gridRow}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); fetchData(); }}
            tintColor={COLORS.primary}
          />
        }
        renderItem={({ item }) => (
          <View
            testID={`heatmap-cell-${item.product_id}`}
            style={[styles.cell, { borderLeftColor: stockColor(item.status) }]}
          >
            <View style={[styles.statusDot, { backgroundColor: stockColor(item.status) }]} />
            <Text style={styles.cellName} numberOfLines={1}>{item.name}</Text>
            <View style={styles.cellRow}>
              <Text style={[styles.cellStock, { color: stockColor(item.status) }]}>
                {item.current_stock}
              </Text>
              <Text style={styles.cellMax}>/ {item.max_stock}</Text>
            </View>
            <View style={styles.stockBar}>
              <View
                style={[
                  styles.stockFill,
                  {
                    width: `${Math.min(100, item.stock_pct)}%`,
                    backgroundColor: stockColor(item.status),
                  },
                ]}
              />
            </View>
            <View style={styles.cellMeta}>
              <Text style={styles.cellMetaText}>
                <Ionicons name="trending-up" size={10} color={COLORS.textMuted} /> {item.demand_velocity}/hr
              </Text>
              <Text style={styles.cellMetaText}>Aisle {item.aisle}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

function StatPill({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <View style={[styles.statPill, { borderColor: color + '40' }]}>
      <View style={[styles.statDot, { backgroundColor: color }]} />
      <Text style={styles.statCount}>{count}</Text>
      <Text style={styles.statLabel}>{label}</Text>
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
  statsBar: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingTop: 12,
    gap: 8,
  },
  statPill: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: COLORS.surface,
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  statDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statCount: {
    fontSize: 14,
    fontWeight: '900',
    color: COLORS.textPrimary,
  },
  statLabel: {
    fontSize: 8,
    color: COLORS.textMuted,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  catList: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 6,
  },
  catBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginRight: 6,
  },
  catBtnActive: {
    backgroundColor: COLORS.primary + '15',
    borderColor: COLORS.primary + '50',
  },
  catText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  catTextActive: {
    color: COLORS.primary,
  },
  gridContent: {
    paddingHorizontal: 12,
    paddingBottom: 20,
  },
  gridRow: {
    gap: 8,
    marginBottom: 8,
  },
  cell: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderLeftWidth: 3,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    position: 'absolute',
    top: 10,
    right: 10,
  },
  cellName: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 6,
    paddingRight: 16,
  },
  cellRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 2,
  },
  cellStock: {
    fontSize: 22,
    fontWeight: '900',
  },
  cellMax: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  stockBar: {
    height: 3,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    marginTop: 6,
  },
  stockFill: {
    height: 3,
    borderRadius: 2,
  },
  cellMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  cellMetaText: {
    fontSize: 10,
    color: COLORS.textMuted,
    fontWeight: '600',
  },
});
