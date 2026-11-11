import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { TelemetryLog, Vehicle } from '../types';
import { MapPin, Navigation } from 'lucide-react';

interface TelemetryMapProps {
  vehicle: Vehicle;
  trajectory: TelemetryLog[];
}

export const TelemetryMap: React.FC<TelemetryMapProps> = ({ vehicle, trajectory }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Inicializa o mapa uma única vez
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Coordenadas centrais da UFRN Campus Central Natal
    const initialCenter: [number, number] = [-5.8365, -35.2052];

    const map = L.map(mapContainerRef.current, {
      center: initialCenter,
      zoom: 15,
      zoomControl: false,
    });

    // Adiciona controle de zoom no canto superior direito
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Tiles do OpenStreetMap estilo CartoDB Dark Matter / OSM Padrão
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;
    layerGroupRef.current = layerGroup;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Atualiza marcadores e polylines sempre que a trajetória mudar
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current) return;

    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    if (!trajectory || trajectory.length === 0) return;

    const latLngs: [number, number][] = trajectory.map(pt => [pt.latitude, pt.longitude]);

    // Desenha a linha de trajetória
    const polyline = L.polyline(latLngs, {
      color: '#10b981', // Emerald
      weight: 4,
      opacity: 0.85,
      smoothFactor: 1
    }).addTo(layerGroup);

    // Ponto inicial
    const startPoint = trajectory[0];
    const startIcon = L.divIcon({
      className: 'custom-pin-start',
      html: `<div style="background-color: #3b82f6; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.5);"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });
    L.marker([startPoint.latitude, startPoint.longitude], { icon: startIcon })
      .bindPopup(`<b>Ponto Inicial</b><br/>Horário: ${new Date(startPoint.recorded_at).toLocaleTimeString()}`)
      .addTo(layerGroup);

    // Ponto atual (mais recente)
    const currentPoint = trajectory[trajectory.length - 1];
    const isExceeded = currentPoint.speed > 80;
    const currentIcon = L.divIcon({
      className: 'custom-pin-current',
      html: `
        <div style="
          background-color: ${isExceeded ? '#ef4444' : '#10b981'}; 
          width: 22px; 
          height: 22px; 
          border-radius: 50%; 
          border: 3px solid white; 
          box-shadow: 0 0 12px ${isExceeded ? 'rgba(239,68,68,0.8)' : 'rgba(16,185,129,0.8)'};
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <div style="background-color: white; width: 6px; height: 6px; border-radius: 50%;"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const popupContent = `
      <div style="font-family: sans-serif; font-size: 12px; color: #1e293b; min-width: 160px;">
        <b style="font-size: 13px;">${vehicle.plate} - ${vehicle.model}</b><br/>
        <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid #e2e8f0;">
          <b>Velocidade:</b> ${currentPoint.speed.toFixed(1)} km/h<br/>
          <b>RPM:</b> ${currentPoint.rpm}<br/>
          <b>Temp. Motor:</b> ${currentPoint.engine_temp.toFixed(1)}°C<br/>
          <b>Horário Coleta:</b> ${new Date(currentPoint.recorded_at).toLocaleTimeString()}<br/>
          ${currentPoint.is_offline_sync ? '<b style="color: #d97706;">[Sincronizado Offline]</b>' : '<span style="color: #10b981;">[Conexão Direta]</span>'}
        </div>
      </div>
    `;

    L.marker([currentPoint.latitude, currentPoint.longitude], { icon: currentIcon })
      .bindPopup(popupContent)
      .addTo(layerGroup)
      .openPopup();

    // Ajusta o zoom para conter o trajeto
    mapInstanceRef.current.fitBounds(polyline.getBounds(), { padding: [40, 40] });
  }, [trajectory, vehicle]);

  const handleCenter = () => {
    if (!mapInstanceRef.current || trajectory.length === 0) return;
    const latest = trajectory[trajectory.length - 1];
    mapInstanceRef.current.setView([latest.latitude, latest.longitude], 16);
  };

  return (
    <div className="relative w-full h-[440px] rounded-xl overflow-hidden border border-slate-800 shadow-xl bg-slate-950">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Trajectory Overlay Info */}
      <div className="absolute top-3 left-3 z-[400] bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-lg p-2.5 shadow-lg text-xs">
        <div className="font-semibold text-slate-200 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-emerald-400" />
          <span>Campus Central UFRN (Natal/RN)</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-3">
          <span>{trajectory.length} pontos de telemetria</span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Online
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> Buffer Offline
          </span>
        </div>
      </div>

      {/* Center button */}
      <button
        onClick={handleCenter}
        title="Centralizar no veículo"
        className="absolute bottom-4 right-4 z-[400] bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700 p-2.5 rounded-lg shadow-lg transition flex items-center gap-1.5 text-xs font-medium"
      >
        <Navigation className="w-3.5 h-3.5 text-emerald-400" />
        <span>Centralizar Veículo</span>
      </button>
    </div>
  );
};
