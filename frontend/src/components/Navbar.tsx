import React from 'react';
import { Truck, Bell, RefreshCw, Database, Radio } from 'lucide-react';
import { Alert } from '../types';

interface NavbarProps {
  unresolvedAlertsCount: number;
  onOpenAlerts: () => void;
  onRefresh: () => void;
  onSeed: () => void;
  isSeeding: boolean;
  networkMode: 'online' | 'offline';
}

export const Navbar: React.FC<NavbarProps> = ({
  unresolvedAlertsCount,
  onOpenAlerts,
  onRefresh,
  onSeed,
  isSeeding,
  networkMode,
}) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand & Edital Tag */}
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-500/10 border border-emerald-500/30 p-2.5 rounded-xl text-emerald-400 flex items-center justify-center">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                EcoFleet <span className="text-xs font-normal text-emerald-400 bg-emerald-950/70 border border-emerald-800 px-2 py-0.5 rounded-full">Telemetria UFRN</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Gestão de Frotas & Telemetria Veicular com Suporte Offline-First
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          {/* Network Indicator */}
          <div className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${
            networkMode === 'online' 
              ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300' 
              : 'bg-amber-950/40 border-amber-800/80 text-amber-300 animate-pulse'
          }`}>
            <Radio className="w-3.5 h-3.5" />
            <span>Rede: {networkMode === 'online' ? 'Online (3G/4G)' : 'Offline (Zona Sem Sinal)'}</span>
          </div>

          {/* Seed Data Button */}
          <button
            onClick={onSeed}
            disabled={isSeeding}
            title="Popular dados de teste do Campus Central UFRN"
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition"
          >
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span>{isSeeding ? 'Populando...' : 'Seed UFRN'}</span>
          </button>

          {/* Refresh Data */}
          <button
            onClick={onRefresh}
            title="Atualizar dados do servidor"
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Alerts Center */}
          <button
            onClick={onOpenAlerts}
            className="relative p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition flex items-center"
          >
            <Bell className="w-4 h-4" />
            {unresolvedAlertsCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 bg-rose-500 text-white font-bold text-[10px] w-5 h-5 rounded-full flex items-center justify-center animate-bounce">
                {unresolvedAlertsCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
