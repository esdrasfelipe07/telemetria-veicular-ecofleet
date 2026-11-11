import React from 'react';
import { Vehicle } from '../types';
import { Truck, CheckCircle, AlertCircle, Wrench } from 'lucide-react';

interface VehicleSelectorProps {
  vehicles: Vehicle[];
  selectedVehicleId: number | null;
  onSelectVehicle: (id: number) => void;
}

export const VehicleSelector: React.FC<VehicleSelectorProps> = ({
  vehicles,
  selectedVehicleId,
  onSelectVehicle,
}) => {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
      {vehicles.map((v) => {
        const isSelected = v.id === selectedVehicleId;
        const statusColors = {
          active: 'text-emerald-400 bg-emerald-950/60 border-emerald-800',
          maintenance: 'text-amber-400 bg-amber-950/60 border-amber-800',
          inactive: 'text-slate-400 bg-slate-800 border-slate-700'
        };

        return (
          <button
            key={v.id}
            onClick={() => onSelectVehicle(v.id)}
            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border text-left transition whitespace-nowrap ${
              isSelected
                ? 'bg-slate-800 border-emerald-500/70 shadow-md ring-1 ring-emerald-500/30'
                : 'bg-slate-900/80 border-slate-800 hover:bg-slate-850 hover:border-slate-700'
            }`}
          >
            <div className={`p-2 rounded-lg ${isSelected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
              <Truck className="w-4 h-4" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-100">{v.plate}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded border font-medium ${statusColors[v.status]}`}>
                  {v.status === 'active' ? 'Ativo' : v.status === 'maintenance' ? 'Oficina' : 'Inativo'}
                </span>
                {v.active_alerts_count > 0 && (
                  <span className="bg-rose-500/20 text-rose-300 border border-rose-800 text-[10px] px-1.5 py-0.2 rounded font-bold">
                    {v.active_alerts_count} alerta(s)
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-400">
                {v.model} • {v.driver_name || 'Sem motorista'}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};
