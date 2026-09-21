export interface OutboxRecord {
  idempotency_key: string;
  entity_type: 'incident_report' | 'water_quality_log' | 'census_event' | 'note_capture';
  payload: Record<string, any>;
  timestamp: string;
  status: 'pending' | 'synced' | 'failed';
}

const LOCAL_OUTBOX_STORAGE_KEY = 'ACARE_MOBILE_OUTBOX';

export class OutboxSyncEngine {
  private static memoryQueue: OutboxRecord[] = [];

  static generateUUID(): string {
    return 'm-' + Date.now().toString(36) + '-' + Math.random().toString(36).substring(2, 9);
  }

  static queueItem(
    entity_type: OutboxRecord['entity_type'],
    payload: Record<string, any>
  ): OutboxRecord {
    const item: OutboxRecord = {
      idempotency_key: OutboxSyncEngine.generateUUID(),
      entity_type,
      payload,
      timestamp: new Date().toISOString(),
      status: 'pending',
    };
    OutboxSyncEngine.memoryQueue.push(item);
    return item;
  }

  static getPendingItems(): OutboxRecord[] {
    return OutboxSyncEngine.memoryQueue.filter((item) => item.status === 'pending');
  }

  static async syncOutboxWithApi(apiBaseUrl: string, authToken: string): Promise<{ syncedCount: number; errorsCount: number }> {
    const pending = OutboxSyncEngine.getPendingItems();
    if (pending.length === 0) {
      return { syncedCount: 0, errorsCount: 0 };
    }

    try {
      const response = await fetch(`${apiBaseUrl}/sync/outbox`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          items: pending.map((p) => ({
            idempotency_key: p.idempotency_key,
            entity_type: p.entity_type,
            payload: p.payload,
            timestamp: p.timestamp,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(`Sync request failed with HTTP ${response.status}`);
      }

      const results = await response.json();
      let syncedCount = 0;
      let errorsCount = 0;

      for (const res of results) {
        const localItem = OutboxSyncEngine.memoryQueue.find((i) => i.idempotency_key === res.idempotency_key);
        if (localItem) {
          if (res.status === 'synced' || res.status === 'duplicate') {
            localItem.status = 'synced';
            syncedCount++;
          } else {
            localItem.status = 'failed';
            errorsCount++;
          }
        }
      }

      return { syncedCount, errorsCount };
    } catch (err) {
      console.warn('[OutboxSyncEngine] Sync failed (device offline or connection timeout):', err);
      return { syncedCount: 0, errorsCount: pending.length };
    }
  }
}
