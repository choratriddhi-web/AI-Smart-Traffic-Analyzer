import logging
from datetime import datetime
from services.mongodb import get_collection

logger = logging.getLogger(__name__)

class AISignalRecommendationEngine:
    """
    Computes intelligent dynamic traffic signal recommendations based on
    real-time vehicle counts, queue lengths, density, and estimated waiting times.
    """

    @staticmethod
    def calculate_recommendation(camera_id: str, vehicle_count: int, max_queue: int, density_category: str, wait_time_sec: int = 45):
        """
        Calculates optimal green duration and recommendation explanation.
        """
        # Baseline minimum and maximum green
        min_green = 15
        max_green = 90
        yellow_duration = 4
        all_red = 2

        # Multipliers
        density_weights = {
            "LOW": 1.0,
            "MODERATE": 1.4,
            "HIGH": 2.0,
            "VERY HIGH": 2.8
        }
        weight = density_weights.get(density_category, 1.2)

        # Dynamic Green duration formula
        # Base (15s) + queue factor (3.2s per queued vehicle) * density multiplier + wait time mitigation
        calculated_green = 15 + (max_queue * 3.2 * weight) + (wait_time_sec * 0.15)
        green_duration = int(max(min_green, min(max_green, round(calculated_green))))

        # Recommended signal state & priority logic
        if density_category == "VERY HIGH" or max_queue >= 10:
            recommended_state = "GREEN_PRIORITY_EXTENDED"
            explanation = (
                f"Severe congestion detected on {camera_id} with {vehicle_count} active vehicles and a "
                f"queue of {max_queue} vehicles. Allocating maximum extended green phase of {green_duration}s "
                f"to prevent arterial gridlock and clear standing queues."
            )
        elif density_category == "HIGH" or max_queue >= 5:
            recommended_state = "GREEN_ADAPTIVE"
            explanation = (
                f"High density ({vehicle_count} vehicles) on {camera_id}. Extending green phase to {green_duration}s "
                f"to dissipate queue length of {max_queue} vehicles efficiently."
            )
        elif density_category == "MODERATE":
            recommended_state = "GREEN_BALANCED"
            explanation = (
                f"Moderate flow detected ({vehicle_count} vehicles). Standard adaptive green timing of {green_duration}s "
                f"recommended to maintain steady vehicular throughput."
            )
        else:
            recommended_state = "GREEN_MINIMAL"
            explanation = (
                f"Low traffic volume ({vehicle_count} vehicles). Short green phase of {green_duration}s is sufficient, "
                f"allowing cross-traffic cycles to advance without unnecessary delay."
            )

        result = {
            "camera_id": camera_id,
            "simulated_label": "SIMULATED AI SIGNAL – NOT CONNECTED TO REAL TRAFFIC LIGHTS",
            "recommended_state": recommended_state,
            "green_duration": green_duration,
            "yellow_duration": yellow_duration,
            "all_red_duration": all_red,
            "inputs": {
                "vehicle_count": vehicle_count,
                "queue_length": max_queue,
                "density_category": density_category,
                "waiting_time_sec": wait_time_sec
            },
            "explanation": explanation,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Persist recommendation
        try:
            signals_col = get_collection("signals")
            signals_col.insert_one({
                "camera_id": camera_id,
                "recommended_state": recommended_state,
                "green_duration": green_duration,
                "vehicle_count": vehicle_count,
                "queue_length": max_queue,
                "density_category": density_category,
                "timestamp": datetime.utcnow()
            })
        except Exception:
            pass

        return result
