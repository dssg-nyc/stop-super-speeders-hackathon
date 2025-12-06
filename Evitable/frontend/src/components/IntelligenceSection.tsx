"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function IntelligenceSection() {
    const [atRisk, setAtRisk] = useState<any[]>([]);
    const [geoStats, setGeoStats] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            try {
                const [riskRes, geoRes] = await Promise.all([
                    fetch("http://localhost:8000/api/intelligence/at-risk"),
                    fetch("http://localhost:8000/api/intelligence/geo-stats")
                ]);
                const riskData = await riskRes.json();
                const geoData = await geoRes.json();

                setAtRisk(riskData.drivers || []);
                setGeoStats(geoData.stats || []);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    if (loading) return <div>Loading Intelligence...</div>;

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* At Risk Table */}
                <Card className="border-yellow-200 bg-yellow-50/30 dark:bg-yellow-900/10 dark:border-yellow-900">
                    <CardHeader>
                        <CardTitle className="text-yellow-700 dark:text-yellow-400">⚠️ Warning Zone (At Risk)</CardTitle>
                        <CardDescription>Drivers with 9-10 points (One violation away from threshold).</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>License</TableHead>
                                    <TableHead>Points</TableHead>
                                    <TableHead>Risk Level</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {atRisk.slice(0, 8).map((d, i) => (
                                    <TableRow key={i}>
                                        <TableCell className="font-mono">{d.license_id}</TableCell>
                                        <TableCell className="font-bold">{d.total_points}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className="border-yellow-500 text-yellow-700">High Risk</Badge>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>

                {/* Geo Stats Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>📍 Violations by County</CardTitle>
                        <CardDescription>Where are the super speeders registered?</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={geoStats}>
                                <XAxis dataKey="county" />
                                <YAxis />
                                <Tooltip
                                    contentStyle={{ backgroundColor: "#333", border: "none", color: "#fff" }}
                                />
                                <Bar dataKey="violation_count" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                                    {geoStats.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index % 2 === 0 ? "#3b82f6" : "#60a5fa"} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
