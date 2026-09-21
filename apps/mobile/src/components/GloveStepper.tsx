import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface GloveStepperProps {
  label: string;
  value: number;
  step?: number;
  min?: number;
  max?: number;
  unit?: string;
  onChange: (val: number) => void;
}

export const GloveStepper: React.FC<GloveStepperProps> = ({
  label,
  value,
  step = 0.1,
  min = 0,
  max = 100,
  unit = '',
  onChange,
}) => {
  const handleDecrement = () => {
    const newVal = Math.max(min, Number((value - step).toFixed(2)));
    onChange(newVal);
  };

  const handleIncrement = () => {
    const newVal = Math.min(max, Number((value + step).toFixed(2)));
    onChange(newVal);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        <TouchableOpacity
          style={[styles.button, styles.btnMinus]}
          onPress={handleDecrement}
          activeOpacity={0.7}
        >
          <Text style={styles.btnText}>-</Text>
        </TouchableOpacity>

        <View style={styles.valueBox}>
          <Text style={styles.valueText}>
            {value.toFixed(1)} {unit}
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.button, styles.btnPlus]}
          onPress={handleIncrement}
          activeOpacity={0.7}
        >
          <Text style={styles.btnText}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    backgroundColor: '#F5F6F7',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D8D9DB',
  },
  label: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#005596',
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  button: {
    width: 60,
    height: 54, // Glove-sized touch target >=48px
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 2,
  },
  btnMinus: {
    backgroundColor: '#58585B',
  },
  btnPlus: {
    backgroundColor: '#005596',
  },
  btnText: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: 'bold',
  },
  valueBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },
  valueText: {
    fontSize: 22,
    fontWeight: 'extrabold',
    color: '#1F1F22',
  },
});
