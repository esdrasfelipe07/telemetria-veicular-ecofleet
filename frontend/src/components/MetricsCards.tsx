import React from 'react';
import { Gauge, Flame, Fuel, BatteryCharging, Navigation, WifiOff } from 'lucide-react';
import { TelemetryLog, Vehicle } from '../types';

interface MetricsCardsProps {
  vehicle: Vehicle;
  latest: TelemetryLog | null | undefined;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ vehicle, latest }) => {
  if (!latest) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        Nenhuma telemetria registrada para este veículo ainda.
      </div>
    );
  }

  const isSpeedHigh = latest.speed > 80;
  const isTempHigh = latest.engine_temp > 100;
  const isBatteryLow = latest.battery_voltage < 11.8;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* Velocidade */}
      <div className={`p-4 rounded-xl border transition ${
        isSpeedHigh 
          ? 'bg-rose-950/30 border-rose-800/80 text-rose-200' 
          : 'bg-slate-900/90 border-slate-800 text-slate-100'
      }`}>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Velocidade</span>
          <Gauge className={`w-4 h-4 ${isSpeedHigh ? 'text-rose-400' : 'text-emerald-400'}`} />
        </div>
        <div className="text-2xl font-bold flex items-baseline gap-1">
          {latest.speed.toFixed(0)} <span className="text-xs font-normal text-slate-400">km/h</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
          <span>Limite: 80 km/h</span>
          {isSpeedHigh && <span className="text-rose-400 font-semibold text-[10px]">EXCESSO</span>}
        </div>
      </div>

      {/* Rotação (RPM) */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-100">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Rotação</span>
          <Navigation className="w-4 h-4 text-blue-400" />
        </div>
        <div className="text-2xl font-bold flex items-baseline gap-1">
          {latest.rpm} <span className="text-xs font-normal text-slate-400">RPM</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Motor em operação
        </div>
      </div>

      {/* Nível de Combustível */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-100">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Combustível</span>
          <Fuel className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-bold flex items-baseline gap-1">
          {latest.fuel_level.toFixed(0)} <span className="text-xs font-normal text-slate-400">%</span>
        </div>
        <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
          <div 
            className="bg-amber-400 h-full rounded-full transition-all" 
            style={{ width: `${Math.min(100, Math.max(0, latest.fuel_level))}%` }}
          />
        </div>
      </div>

      {/* Temperatura do Motor */}
      <div className={`p-4 rounded-xl border transition ${
        isTempHigh 
          ? 'bg-rose-950/30 border-rose-800/80 text-rose-200' 
          : 'bg-slate-900/90 border-slate-800 text-slate-100'
      }`}>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Temperatura</span>
          <Flame className={`w-4 h-4 ${isTempHigh ? 'text-rose-400' : 'text-orange-400'}`} />
        </div>
        <div className="text-2xl font-bold flex items-baseline gap-1">
          {latest.engine_temp.toFixed(0)} <span className="text-xs font-normal text-slate-400">°C</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          {isTempHigh ? <span className="text-rose-400 font-semibold">Superaquecido!</span> : 'Faixa normal'}
        </div>
      </div>

      {/* Tensão da Bateria */}
      <div className={`p-4 rounded-xl border transition ${
        isBatteryLow 
          ? 'bg-amber-950/30 border-amber-800/80 text-amber-200' 
          : 'bg-slate-900/90 border-slate-800 text-slate-100'
      }`}>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Bateria</span>
          <BatteryCharging className={`w-4 h-4 ${isBatteryLow ? 'text-amber-400' : 'text-emerald-400'}`} />
        </div>
        <div className="text-2xl font-bold flex items-baseline gap-1">
          {latest.battery_voltage.toFixed(1)} <span className="text-xs font-normal text-slate-400">V</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Alternador ativo
        </div>
      </div>

      {/* Odômetro & Modo de Origem */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-100 flex flex-col justify-between">
        <div>
          <div className="text-xs text-slate-400 mb-1">Odômetro</div>
          <div className="text-xl font-bold flex items-baseline gap-1">
            {latest.odometer.toFixed(0)} <span className="text-xs font-normal text-slate-400">km</span>
          </div>
        </div>
        <div className="mt-1">
          {latest.is_offline_sync ? (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-amber-950/80 text-amber-400 border border-amber-800/60 px-1.5 py-0.5 rounded">
              <WifiOff className="w-2.5 h-2.5" /> Sinc. Offline
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-1.5 py-0.5 rounded">
              Tempo Real
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
