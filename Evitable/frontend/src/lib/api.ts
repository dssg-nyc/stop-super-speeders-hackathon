export interface ViolatorDriver {
    license_id: string;
    total_points: number;
    violation_count: number;
    last_violation: string;
}

export interface ViolatorPlate {
    plate: string;
    state: string;
    ticket_count: number;
    last_ticket: string;
}

const API_BASE = "http://localhost:8000/api";

export async function fetchDrivers(): Promise<ViolatorDriver[]> {
    try {
        const res = await fetch(`${API_BASE}/violators/drivers`);
        if (!res.ok) throw new Error("Failed to fetch drivers");
        const data = await res.json();
        return data.violators || [];
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function fetchPlates(): Promise<ViolatorPlate[]> {
    try {
        const res = await fetch(`${API_BASE}/violators/plates`);
        if (!res.ok) throw new Error("Failed to fetch plates");
        const data = await res.json();
        return data.violators || [];
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function fetchRecentDrivers(): Promise<ViolatorDriver[]> {
    try {
        const res = await fetch(`${API_BASE}/violators/drivers/recent`);
        if (!res.ok) throw new Error("Failed to fetch recent drivers");
        const data = await res.json();
        return data.violators || [];
    } catch (error) {
        console.error(error);
        return [];
    }
}
