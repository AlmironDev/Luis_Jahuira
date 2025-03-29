import React, { useState } from 'react';
import axios from 'axios';

const PostureConfigForm = () => {
    const [config, setConfig] = useState({
        detectorType: 'posture',
        legAngleThreshold: 307,
        neckAngleThreshold: 45,
        alertDuration: 5
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post('http://localhost:8000/update-config/', {
                detector_type: config.detectorType,
                config: {
                    leg_angle_threshold: config.legAngleThreshold,
                    neck_angle_threshold: config.neckAngleThreshold,
                    alert_duration: config.alertDuration
                }
            });
            alert('Configuración actualizada!');
        } catch (error) {
            console.error('Error updating config:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h2>Ajustar Parámetros de Detección</h2>

            <div>
                <label>Tipo de Detector:</label>
                <select
                    value={config.detectorType}
                    onChange={(e) => setConfig({ ...config, detectorType: e.target.value })}
                >
                    <option value="posture">Postura</option>
                    <option value="hands">Manos</option>
                </select>
            </div>

            <div>
                <label>Ángulo mínimo de piernas:</label>
                <input
                    type="number"
                    value={config.legAngleThreshold}
                    onChange={(e) => setConfig({ ...config, legAngleThreshold: e.target.value })}
                />
            </div>

            <div>
                <label>Ángulo máximo de cuello:</label>
                <input
                    type="number"
                    value={config.neckAngleThreshold}
                    onChange={(e) => setConfig({ ...config, neckAngleThreshold: e.target.value })}
                />
            </div>

            <div>
                <label>Duración antes de alerta (segundos):</label>
                <input
                    type="number"
                    value={config.alertDuration}
                    onChange={(e) => setConfig({ ...config, alertDuration: e.target.value })}
                />
            </div>

            <button type="submit">Guardar Configuración</button>
        </form>
    );
};

export default PostureConfigForm;