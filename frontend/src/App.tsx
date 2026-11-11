import React, { useState, useEffect, useCallback } from 'react';
import { Vehicle, TelemetryLog, Alert } from './types';
import { api } from './api';
import { Navbar } from './components/Navbar';
import { VehicleSelector } from './components/VehicleSelector';
import { MetricsCards } from './components/MetricsCards';
import { TelemetryMap } from './components/TelemetryMap';
import { OfflineSimulator } from './components/OfflineSimulator';
import { AlertsModal } from './components/AlertsModal';
import { Truck, RefreshCw, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [trajectory, setTrajectory] = useState<TelemetryLog[]>([]);
  const [unresolvedAlertsCount, setUnresolvedAlertsCount] = useState<number>(0);
  const [isAlertsOpen, setIsAlertsOpen] = useState(false);
  const [networkMode, setNetworkMode] = useState<'online' | 'offline'>('online');
  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Carrega lista de veículos e alertas
  const loadFleetData = useCallback(async () => {
    try {
      setError(null);
      const [fetchedVehicles, fetchedAlerts] = await Promise.all([
        api.getVehicles(),
        api.getAlerts(true)
      ]);

      setVehicles(fetchedVehicles);
      setUnresolvedAlertsCount(fetchedAlerts.length);

      if (fetchedVehicles.length > 0 && selectedVehicleId === null) {
        setSelectedVehicleId(fetchedVehicles[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setError('Falha na comunicação com o backend FastAPI. Verifique se o servidor está ativo na porta 8000.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedVehicleId]);

  // Carrega o trajeto histórico do veículo selecionado
  const loadTrajectory = useCallback(async (vehicleId: number) => {
    try {
      const data = await api.getVehicleTrajectory(vehicleId, 150);
      setTrajectory(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    loadFleetData();
  }, [loadFleetData]);

  useEffect(() => {
    if (selectedVehicleId) {
      loadTrajectory(selectedVehicleId);
    }
  }, [selectedVehicleId, loadTrajectory]);

  // Handler para quando nova telemetria for enviada ou sincronizada em lote
  const handleTelemetryUpdated = () => {
    loadFleetData();
    if (selectedVehicleId) {
      loadTrajectory(selectedVehicleId);
    }
  };

  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      await api.seedData();
      await loadFleetData();
      if (selectedVehicleId) {
        await loadTrajectory(selectedVehicleId);
      }
    } catch (err: any) {
      alert(`Erro no seed: ${err.message}`);
    } finally {
      setIsSeeding(false);
    }
  };

  const currentVehicle = vehicles.find(v => v.id === selectedVehicleId);
  const latestTelemetry = trajectory.length > 0 
    ? trajectory[trajectory.length - 1] 
    : currentVehicle?.latest_telemetry;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <Navbar
        unresolvedAlertsCount={unresolvedAlertsCount}
        onOpenAlerts={() => setIsAlertsOpen(true)}
        onRefresh={loadFleetData}
        onSeed={handleSeed}
        isSeeding={isSeeding}
        networkMode={networkMode}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-200 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={loadFleetData}
              className="px-3 py-1 bg-rose-900 hover:bg-rose-800 rounded-lg text-xs font-medium transition"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && vehicles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
            <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
            <p className="text-sm">Carregando telemetria da frota UFRN...</p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800 p-8 space-y-4">
            <Truck className="w-12 h-12 text-slate-500 mx-auto" />
            <h3 className="text-lg font-bold text-slate-200">Nenhum veículo encontrado</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Clique no botão abaixo para popular automaticamente o sistema com a frota e trajetos de exemplo da UFRN.
            </p>
            <button
              onClick={handleSeed}
              disabled={isSeeding}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition inline-flex items-center gap-2"
            >
              {isSeeding ? 'Carregando...' : 'Popular Demonstração (UFRN)'}
            </button>
          </div>
        ) : (
          <>
            {/* Seletor de Veículo da Frota */}
            <div>
              <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Veículos em Operação (Campus UFRN)
              </div>
              <VehicleSelector
                vehicles={vehicles}
                selectedVehicleId={selectedVehicleId}
                onSelectVehicle={setSelectedVehicleId}
              />
            </div>

            {currentVehicle && (
              <>
                {/* Cards de Métricas em Tempo Real */}
                <MetricsCards vehicle={currentVehicle} latest={latestTelemetry} />

                {/* Simulador Interativo de Conectividade e Cache Offline */}
                <OfflineSimulator
                  vehicle={currentVehicle}
                  networkMode={networkMode}
                  onToggleNetwork={setNetworkMode}
                  onTelemetryUpdated={handleTelemetryUpdated}
                />

                {/* Mapa Interativo de Trajetória */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                      Rastreamento Georreferenciado & Histórico de Rota
                    </h3>
                    <span className="text-xs text-slate-400">
                      Coordenadas atualizadas a cada envio de telemetria
                    </span>
                  </div>
                  <TelemetryMap vehicle={currentVehicle} trajectory={trajectory} />
                </div>
              </>
            )}
          </>
        )}
      </main>

      {/* Modal de Alertas */}
      <AlertsModal
        isOpen={isAlertsOpen}
        onClose={() => setIsAlertsOpen(false)}
        onAlertResolved={loadFleetData}
      />

      {/* Footer com Metadados do Edital */}
      <footer className="bg-slate-900/60 border-t border-slate-800/80 px-4 py-3 text-center text-xs text-slate-500">
        Desenvolvido para o Edital da UFRN — Vaga 5: Desenvolvedor Júnior Full-Stack (Telemetria Veicular & Offline-First)
      </footer>
    </div>
  );
};
export default App;
