import React, { useState, useEffect } from 'react';
import { Alert } from '../types';
import { api } from '../api';
import { X, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface AlertsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAlertResolved: () => void;
}

export const AlertsModal: React.FC<AlertsModalProps> = ({
  isOpen,
  onClose,
  onAlertResolved,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterUnresolved, setFilterUnresolved] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(filterUnresolved);
      setAlerts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAlerts();
    }
  }, [isOpen, filterUnresolved]);

  const handleResolve = async (id: number) => {
    try {
      await api.resolveAlert(id);
      fetchAlerts();
      onAlertResolved();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Central de Alertas e Anomalias</h2>
              <p className="text-xs text-slate-400">Detecção automática por limites de telemetria</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter bar */}
        <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs">
          <span className="text-slate-400">Total listado: {alerts.length}</span>
          <label className="flex items-center gap-2 cursor-pointer text-slate-300">
            <input
              type="checkbox"
              checked={filterUnresolved}
              onChange={(e) => setFilterUnresolved(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-0"
            />
            <span>Apenas não resolvidos</span>
          </label>
        </div>

        {/* List */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {loading ? (
            <div className="text-center py-8 text-slate-500 text-sm">Carregando alertas...</div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              Nenhum alerta {filterUnresolved ? 'pendente' : 'registrado'}.
            </div>
          ) : (
            alerts.map((alert) => {
              const severityBadge = {
                CRITICAL: 'bg-rose-950/80 border-rose-800 text-rose-300',
                HIGH: 'bg-orange-950/80 border-orange-800 text-orange-300',
                MEDIUM: 'bg-amber-950/80 border-amber-800 text-amber-300',
                LOW: 'bg-blue-950/80 border-blue-800 text-blue-300'
              }[alert.severity] || 'bg-slate-800 text-slate-300';

              return (
                <div
                  key={alert.id}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-950/50 flex items-start justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${severityBadge}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {alert.alert_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-medium">{alert.message}</p>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-500 pt-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(alert.triggered_at).toLocaleString()}</span>
                    </div>
                  </div>

                  {!alert.resolved ? (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-emerald-950/80 hover:text-emerald-300 border border-slate-700 hover:border-emerald-700 text-slate-300 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Resolver</span>
                    </button>
                  ) : (
                    <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> Resolvido
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
