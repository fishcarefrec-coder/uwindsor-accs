import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  ScrollView,
  StyleSheet,
  Switch,
  Alert,
} from 'react-native';
import { GloveStepper } from '../components/GloveStepper';
import { OutboxSyncEngine, OutboxRecord } from '../services/outboxSync';

export const OfflineCaptureScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'water_quality' | 'incident' | 'note'>('water_quality');

  // Water Quality state
  const [tankNumber, setTankNumber] = useState('Tank 1');
  const [ph, setPh] = useState(7.4);
  const [temperature, setTemperature] = useState(26.5);
  const [dissolvedOxygen, setDissolvedOxygen] = useState(7.2);

  // Incident state
  const [problemDescription, setProblemDescription] = useState('');
  const [treatment, setTreatment] = useState('');
  const [vetContacted, setVetContacted] = useState(false);
  const [photoCaptured, setPhotoCaptured] = useState(false);

  // Note state
  const [noteContent, setNoteContent] = useState('');

  // Sync state
  const [pendingCount, setPendingCount] = useState(OutboxSyncEngine.getPendingItems().length);
  const [syncStatus, setSyncStatus] = useState<string>('Ready');

  const handleSaveWaterQuality = () => {
    OutboxSyncEngine.queueItem('water_quality_log', {
      tank_id: tankNumber,
      ph,
      temperature,
      dissolved_oxygen: dissolvedOxygen,
      comments: 'Captured via ACARE Tablet Mobile',
    });
    setPendingCount(OutboxSyncEngine.getPendingItems().length);
    Alert.alert('Saved to Offline Outbox', `Water Quality reading for ${tankNumber} queued.`);
  };

  const handleSaveIncident = () => {
    if (!problemDescription.trim()) {
      Alert.alert('Validation Error', 'Please enter a problem description.');
      return;
    }
    OutboxSyncEngine.queueItem('incident_report', {
      tank_id: tankNumber,
      problem_description: problemDescription,
      treatment_solution: treatment,
      vet_contacted: vetContacted,
      photo_attachment_url: photoCaptured ? 'data:image/jpeg;base64,sample_photo_data' : null,
    });
    setPendingCount(OutboxSyncEngine.getPendingItems().length);
    setProblemDescription('');
    setTreatment('');
    Alert.alert('Saved to Offline Outbox', `Incident Report for ${tankNumber} queued.`);
  };

  const handleSaveNote = () => {
    if (!noteContent.trim()) {
      Alert.alert('Validation Error', 'Please enter a note.');
      return;
    }
    OutboxSyncEngine.queueItem('note_capture', {
      tank_id: tankNumber,
      note: noteContent,
    });
    setPendingCount(OutboxSyncEngine.getPendingItems().length);
    setNoteContent('');
    Alert.alert('Saved to Offline Outbox', 'Note saved to outbox queue.');
  };

  const handleTriggerSync = async () => {
    setSyncStatus('Syncing with API...');
    const result = await OutboxSyncEngine.syncOutboxWithApi('http://localhost:8000/api/v1', 'demo-token');
    setPendingCount(OutboxSyncEngine.getPendingItems().length);
    setSyncStatus(`Sync finished: ${result.syncedCount} synced, ${result.errorsCount} pending/retry.`);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>ACARE Tablet Offline Capture</Text>
        <Text style={styles.subtitle}>University of Windsor Aquatic Facility</Text>

        <View style={styles.outboxBanner}>
          <Text style={styles.outboxText}>
            Pending Outbox Queue: <Text style={styles.badgeText}>{pendingCount} items</Text>
          </Text>
          <TouchableOpacity style={styles.syncBtn} onPress={handleTriggerSync}>
            <Text style={styles.syncBtnText}>Sync Outbox</Text>
          </TouchableOpacity>
        </View>
        {syncStatus ? <Text style={styles.statusText}>{syncStatus}</Text> : null}
      </View>

      {/* Navigation Tabs */}
      <View style={styles.tabContainer}>
        {[
          { id: 'water_quality', label: 'Water Quality' },
          { id: 'incident', label: 'Incident Report' },
          { id: 'note', label: 'Quick Note' },
        ].map((t) => (
          <TouchableOpacity
            key={t.id}
            style={[styles.tabBtn, activeTab === t.id && styles.tabBtnActive]}
            onPress={() => setActiveTab(t.id as any)}
          >
            <Text style={[styles.tabBtnText, activeTab === t.id && styles.tabBtnTextActive]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Form Content */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Room 101 — Bound Tablet Device</Text>
        <Text style={styles.fieldLabel}>Target Tank</Text>
        <TextInput
          style={styles.textInput}
          value={tankNumber}
          onChangeText={setTankNumber}
          placeholder="e.g. Tank 1"
        />

        {activeTab === 'water_quality' && (
          <View>
            <GloveStepper label="pH Reading" value={ph} step={0.1} min={5.0} max={10.0} unit="pH" onChange={setPh} />
            <GloveStepper label="Temperature" value={temperature} step={0.5} min={10.0} max={35.0} unit="°C" onChange={setTemperature} />
            <GloveStepper label="Dissolved Oxygen" value={dissolvedOxygen} step={0.2} min={0.0} max={15.0} unit="mg/L" onChange={setDissolvedOxygen} />

            <TouchableOpacity style={styles.submitBtn} onPress={handleSaveWaterQuality}>
              <Text style={styles.submitBtnText}>Save Reading (Offline Queue)</Text>
            </TouchableOpacity>
          </View>
        )}

        {activeTab === 'incident' && (
          <View>
            {vetContacted && (
              <View style={styles.vetBanner}>
                <Text style={styles.vetBannerText}>⚠️ VETERINARIAN CONTACTED FLAG ACTIVE</Text>
              </View>
            )}

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Contacted Veterinarian?</Text>
              <Switch value={vetContacted} onValueChange={setVetContacted} trackColor={{ false: '#767577', true: '#C0392B' }} />
            </View>

            <Text style={styles.fieldLabel}>Problem Description</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              value={problemDescription}
              onChangeText={setProblemDescription}
              placeholder="Describe symptoms or water quality anomaly..."
              multiline
            />

            <Text style={styles.fieldLabel}>Immediate Treatment Taken</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              value={treatment}
              onChangeText={setTreatment}
              placeholder="Actions performed..."
              multiline
            />

            <TouchableOpacity
              style={[styles.photoBtn, photoCaptured && styles.photoBtnSuccess]}
              onPress={() => setPhotoCaptured(!photoCaptured)}
            >
              <Text style={styles.photoBtnText}>
                {photoCaptured ? '✓ Photo Attachment Captured' : '📷 Attach Photo from Tablet Camera'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.submitBtn} onPress={handleSaveIncident}>
              <Text style={styles.submitBtnText}>Queue Incident Report (Offline)</Text>
            </TouchableOpacity>
          </View>
        )}

        {activeTab === 'note' && (
          <View>
            <Text style={styles.fieldLabel}>Offline Room / Tank Note</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              value={noteContent}
              onChangeText={setNoteContent}
              placeholder="Capture room notes, observations, or maintenance reminders..."
              multiline
            />

            <TouchableOpacity style={styles.submitBtn} onPress={handleSaveNote}>
              <Text style={styles.submitBtnText}>Save Quick Note</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F6F7',
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#005596',
  },
  subtitle: {
    fontSize: 12,
    color: '#58585B',
  },
  outboxBanner: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#E6F0F7',
    padding: 12,
    borderRadius: 10,
    marginTop: 10,
    borderWidth: 1,
    borderColor: '#005596',
  },
  outboxText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1F1F22',
  },
  badgeText: {
    color: '#005596',
    fontWeight: 'extrabold',
  },
  syncBtn: {
    backgroundColor: '#005596',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  syncBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 12,
  },
  statusText: {
    fontSize: 11,
    color: '#58585B',
    marginTop: 4,
    fontStyle: 'italic',
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D8D9DB',
    alignItems: 'center',
  },
  tabBtnActive: {
    backgroundColor: '#005596',
    borderColor: '#005596',
  },
  tabBtnText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#58585B',
  },
  tabBtnTextActive: {
    color: '#FFFFFF',
  },
  card: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D8D9DB',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#005596',
    marginBottom: 12,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#1F1F22',
    marginTop: 10,
    marginBottom: 4,
  },
  textInput: {
    backgroundColor: '#FAFAFA',
    borderWidth: 1,
    borderColor: '#D8D9DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1F1F22',
  },
  textArea: {
    height: 90,
    textAlignVertical: 'top',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 12,
  },
  switchLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1F1F22',
  },
  vetBanner: {
    backgroundColor: '#C0392B',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
  },
  vetBannerText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    textAlign: 'center',
    fontSize: 12,
  },
  photoBtn: {
    backgroundColor: '#58585B',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 12,
  },
  photoBtnSuccess: {
    backgroundColor: '#1E8A4C',
  },
  photoBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  submitBtn: {
    backgroundColor: '#005596',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  submitBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
