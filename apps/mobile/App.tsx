import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import { OfflineCaptureScreen } from './src/screens/OfflineCaptureScreen';

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#005596" />
      <OfflineCaptureScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#005596',
  },
});
