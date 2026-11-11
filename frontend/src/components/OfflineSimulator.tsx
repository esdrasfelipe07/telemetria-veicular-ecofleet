import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, Send, Play, Pause, AlertTriangle, CheckCircle2, Layers } from 'lucide-react';
import { Vehicle, TelemetryLog } from '../types';
import { offlineQueue } from '../utils/offlineQueue';
import { api } from '../api';

interface OfflineSimulatorProps {
  vehicle: Vehicle;
  networkMode: 'online' | 'offline';
  onToggleNetwork: (mode: 'online' | 'offline') => void;
  onTelemetryUpdated: () => void;
}

export const OfflineSimulator: React.FC<OfflineSimulatorProps> = ({
  vehicle,
  networkMode,
  onToggleNetwork,
  onTelemetryUpdated,
}) => {
  const [cachedCount, setCachedCount] = useState<number>(offlineQueue.getCount());
  const [isAutoSimulating, setIsAutoSimulating] = useState(false);
  const [lastSyncMsg, setLastSyncMsg] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Simulação de deslocamento incremental em torno do anel viário
  const [stepIndex, setStepIndex] = useState(0);

  // Caminho circular simulado de alta precisão ao longo do asfalto do Anel Viário da UFRN
  const waypoints = [
    { lat: -5.8378, lng: -35.2053, speed: 30.0, rpm: 1400 }, // Rotatória Reitoria / Praça Cívica
    { lat: -5.8390, lng: -35.2050, speed: 38.0, rpm: 1600 }, // Anel Viário descendo em frente ao CCHLA
    { lat: -5.8405, lng: -35.2043, speed: 42.0, rpm: 1750 }, // Setor de Aulas II
    { lat: -5.8420, lng: -35.2034, speed: 46.0, rpm: 1900 }, // Acesso Biblioteca Central / RU
    { lat: -5.8429, lng: -35.2028, speed: 40.0, rpm: 1650 }, // Rotatória Sul / Centro de Biociências
    { lat: -5.8433, lng: -35.2015, speed: 45.0, rpm: 1800 }, // Anel Viário Sul (Setor de Aulas IV)
    { lat: -5.8437, lng: -35.1995, speed: 48.0, rpm: 1900 }, // Anel Sul (Área Tecnológica / ECT)
    { lat: -5.8441, lng: -35.1970, speed: 50.0, rpm: 2000 }, // Curva Sudeste do Anel Viário
    { lat: -5.8425, lng: -35.1953, speed: 52.0, rpm: 2050 }, // Anel Viário Leste (Reta)
    { lat: -5.8405, lng: -35.1951, speed: 84.0, rpm: 2900 }, // Reta Anel Leste (Alerta de Velocidade 84 km/h)
    { lat: -5.8385, lng: -35.1962, speed: 50.0, rpm: 2000 }, // Anel Leste aproximando do Ginásio Poliesportivo
    { lat: -5.8368, lng: -35.1975, speed: 42.0, rpm: 1750 }, // Curva da Pista de Atletismo
    { lat: -5.8350, lng: -35.1998, speed: 38.0, rpm: 1600 }, // Anel Viário Norte (Parque Tecnológico / Bosque)
    { lat: -5.8335, lng: -35.2020, speed: 35.0, rpm: 1500 }, // Proximidades do IMD
    { lat: -5.8325, lng: -35.2036, speed: 32.0, rpm: 1450 }, // Curva Norte (Acesso Solon de Miranda Galvão)
    { lat: -5.8340, lng: -35.2052, speed: 35.0, rpm: 1500 }, // Sentido Reitoria
    { lat: -5.8360, lng: -35.2057, speed: 32.0, rpm: 1450 }, // Chegada à Praça Cívica
    { lat: -5.8378, lng: -35.2053, speed: 30.0, rpm: 1400 }, // Retorno à Rotatória da Reitoria (Loop Fechado)
  ];

  const generateNextPoint = async () => {
    const nextIdx = (stepIndex + 1) % waypoints.length;
    setStepIndex(nextIdx);
    const wp = waypoints[nextIdx];

    const currentLatest = vehicle.latest_telemetry;
    const currentFuel = currentLatest ? Math.max(5, currentLatest.fuel_level - 0.2) : 75.0;
    const currentOdo = currentLatest ? currentLatest.odometer + 0.15 : 14250.0;

    const pointData: Omit<TelemetryLog, 'id' | 'ingested_at'> = {
      vehicle_id: vehicle.id,
      recorded_at: new Date().toISOString(),
      latitude: wp.lat,
      longitude: wp.lng,
      speed: wp.speed,
      rpm: wp.rpm,
      fuel_level: Number(currentFuel.toFixed(1)),
      engine_temp: wp.speed > 80 ? 98.5 : 91.0,
      battery_voltage: 12.6,
      odometer: Number(currentOdo.toFixed(2)),
      is_offline_sync: networkMode === 'offline'
    };

    if (networkMode === 'offline') {
      // Guarda no cache local (localStorage/IndexedDB)
      offlineQueue.enqueue(pointData);
      setCachedCount(offlineQueue.getCount());
      setLastSyncMsg(`Ponto gravado no buffer local offline (${new Date().toLocaleTimeString()}).`);
    } else {
      // Envia diretamente ao servidor via API REST
      try {
        await api.sendSingleTelemetry(pointData);
        onTelemetryUpdated();
        setLastSyncMsg(`Ponto transmitido com sucesso via 3G/4G (${new Date().toLocaleTimeString()}).`);
      } catch (err) {
        console.error(err);
        // Fallback automático para fila se o request falhar
        offlineQueue.enqueue(pointData);
        setCachedCount(offlineQueue.getCount());
        setLastSyncMsg('Falha de conexão com a API: ponto guardado no cache local de emergência.');
      }
    }
  };

  // Sincroniza todo o lote guardado no cache offline
  const handleSyncBatch = async () => {
    const items = offlineQueue.getAll();
    if (items.length === 0) return;

    setIsSyncing(true);
    try {
      const result = await api.sendTelemetryBatch(items);
      offlineQueue.clear();
      setCachedCount(0);
      setLastSyncMsg(
        `Sucesso: Lote de ${result.received_count} medições sincronizado com o servidor! (${result.alerts_triggered} alertas acionados).`
      );
      onTelemetryUpdated();
    } catch (err: any) {
      setLastSyncMsg(`Erro na sincronização em lote: ${err.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  // Loop de simulação automática
  useEffect(() => {
    let interval: any = null;
    if (isAutoSimulating) {
      interval = setInterval(() => {
        generateNextPoint();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAutoSimulating, stepIndex, networkMode, vehicle]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Simulador de Rastreador & Conectividade Reduzida
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Demonstração prática do armazenamento em cache local com envio em lote (Batch Sync)
          </p>
        </div>

        {/* Toggle Online / Offline */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Status de Conectividade:</span>
          <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800">
            <button
              onClick={() => {
                onToggleNetwork('online');
                // Se voltar a ficar online e houver itens em buffer, sugere ou executa sync
                if (cachedCount > 0) {
                  handleSyncBatch();
                }
              }}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition ${
                networkMode === 'online'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Wifi className="w-3.5 h-3.5" />
              <span>Online (3G/4G)</span>
            </button>
            <button
              onClick={() => onToggleNetwork('offline')}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition ${
                networkMode === 'offline'
                  ? 'bg-amber-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <WifiOff className="w-3.5 h-3.5" />
              <span>Offline (Sem Sinal)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Simulator Controls & Actions */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {/* Gerar 1 ponto */}
          <button
            onClick={generateNextPoint}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-lg text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5 text-blue-400" />
            <span>Gerar Leitura GPS</span>
          </button>

          {/* Toggle Auto */}
          <button
            onClick={() => setIsAutoSimulating(!isAutoSimulating)}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              isAutoSimulating
                ? 'bg-rose-900/60 hover:bg-rose-900 border border-rose-700 text-rose-200'
                : 'bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-700 text-emerald-200'
            }`}
          >
            {isAutoSimulating ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pausar Simulação Contínua</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Iniciar Simulação Contínua (3s)</span>
              </>
            )}
          </button>
        </div>

        {/* Sync Batch Button */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-slate-300 font-medium flex items-center gap-1.5">
              <span>Cache Local:</span>
              <span className={`px-2 py-0.5 rounded-full font-bold text-xs ${
                cachedCount > 0 ? 'bg-amber-950 border border-amber-800 text-amber-300 animate-pulse' : 'bg-slate-800 text-slate-400'
              }`}>
                {cachedCount} pacotes pendentes
              </span>
            </div>
          </div>

          <button
            onClick={handleSyncBatch}
            disabled={cachedCount === 0 || isSyncing}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              cachedCount > 0
                ? 'bg-amber-500 hover:bg-amber-600 text-slate-950 shadow-md cursor-pointer'
                : 'bg-slate-800 text-slate-500 border border-slate-800 cursor-not-allowed'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{isSyncing ? 'Sincronizando Lote...' : 'Descarregar Cache no Servidor (Batch)'}</span>
          </button>
        </div>
      </div>

      {/* Status Output Bar */}
      {lastSyncMsg && (
        <div className="mt-3.5 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 flex items-center justify-between">
          <span className="truncate">{lastSyncMsg}</span>
          <span className="text-[10px] text-slate-500 ml-2 whitespace-nowrap">POST /api/v1/telemetry/batch</span>
        </div>
      )}
    </div>
  );
};
