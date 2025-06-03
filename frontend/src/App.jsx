import React, { useState, useEffect } from 'react';

const initialAssets = [
  {
    asset_id: 'A1',
    asset_type: 'Tractor',
    current_location: { lat: 34.05, lon: -118.25 },
    rental_status: 'available',
    eta: '2h',
  },
  {
    asset_id: 'B2',
    asset_type: 'Seeder',
    current_location: { lat: 35.68, lon: -119.5 },
    rental_status: 'rented',
    eta: '1h',
  },
  {
    asset_id: 'C3',
    asset_type: 'Harvester',
    current_location: { lat: 36.17, lon: -120.0 },
    rental_status: 'returned',
    eta: '3h',
  },
];

function randomDelta() {
  return (Math.random() - 0.5) * 0.01;
}

export default function App() {
  const [assets, setAssets] = useState(initialAssets);

  useEffect(() => {
    const interval = setInterval(() => {
      setAssets(current =>
        current.map(asset => ({
          ...asset,
          current_location: {
            lat: asset.current_location.lat + randomDelta(),
            lon: asset.current_location.lon + randomDelta(),
          },
        }))
      );
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleStatus = index => {
    setAssets(current => {
      const updated = [...current];
      const status = updated[index].rental_status;
      updated[index].rental_status =
        status === 'available' ? 'rented' : status === 'rented' ? 'returned' : 'available';
      return updated;
    });
  };

  return (
    <div className="flex h-full">
      <div className="w-64 bg-gray-100 p-4 overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Assets</h2>
        {assets.map((asset, idx) => (
          <div
            key={asset.asset_id}
            className="mb-4 p-2 border rounded cursor-pointer hover:bg-gray-200"
            onClick={() => toggleStatus(idx)}
          >
            <div className="font-semibold">{asset.asset_id} - {asset.asset_type}</div>
            <div className="text-sm">Lat: {asset.current_location.lat.toFixed(4)}, Lon: {asset.current_location.lon.toFixed(4)}</div>
            <div className="text-sm">Status: {asset.rental_status}</div>
            <div className="text-sm">ETA: {asset.eta}</div>
          </div>
        ))}
      </div>
      <div className="flex-1 bg-green-200 flex items-center justify-center text-2xl">
        Map Placeholder
      </div>
    </div>
  );
}
