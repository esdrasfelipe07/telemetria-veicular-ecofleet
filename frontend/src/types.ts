export interface TelemetryLog {
  id?: number;
  vehicle_id: number;
  recorded_at: string;
  ingested_at?: string;
  latitude: number;
  longitude: number;
  speed: number;
  rpm: number;
  fuel_level: number;
  engine_temp: number;
  battery_voltage: number;
  odometer: number;
  is_offline_sync?: boolean;
}

export interface Vehicle {
  id: number;
  plate: string;
  model: string;
  brand: string;
  year: number;
  status: 'active' | 'maintenance' | 'inactive';
  driver_name?: string;
  created_at: string;
  latest_telemetry?: TelemetryLog | null;
  active_alerts_count: number;
}

export interface Alert {
  id: number;
  vehicle_id: number;
  alert_type: string;
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  triggered_at: string;
  resolved: boolean;
}

export interface BatchSyncResult {
  status: string;
  message: string;
  received_count: number;
  persisted_count: number;
  alerts_triggered: number;
}
