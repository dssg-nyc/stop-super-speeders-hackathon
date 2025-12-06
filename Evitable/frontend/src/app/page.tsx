"use client";

import { useEffect, useState } from "react";
import { fetchDrivers, fetchPlates, fetchRecentDrivers, ViolatorDriver, ViolatorPlate } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";
import UploadSection from "@/components/UploadSection";
import IntelligenceSection from "@/components/IntelligenceSection";

export default function Dashboard() {
  const [drivers, setDrivers] = useState<ViolatorDriver[]>([]);
  const [recentDrivers, setRecentDrivers] = useState<ViolatorDriver[]>([]);
  const [plates, setPlates] = useState<ViolatorPlate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const [d, p, r] = await Promise.all([fetchDrivers(), fetchPlates(), fetchRecentDrivers()]);
      setDrivers(d);
      setPlates(p);
      setRecentDrivers(r);
      setLoading(false);
    }
    loadData();
  }, []);

  if (loading) return <div className="p-10 text-center">Loading Data...</div>;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Stop Super Speeders 🛑
            </h1>
            <p className="text-slate-500 mt-2 text-lg">
              Families for Safe Streets Threshold Monitor
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <a href="http://localhost:8000/api/violators/drivers/download">Export Drivers (24mo)</a>
            </Button>
            <Button variant="outline" asChild>
              <a href="http://localhost:8000/api/violators/plates/download">Export Plates (12mo)</a>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900">
            <CardHeader>
              <CardTitle className="text-red-700 dark:text-red-400">Drivers Above Threshold</CardTitle>
              <CardDescription>11+ Points in 24 Months</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold text-red-900 dark:text-red-100">
                {drivers.length}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-900">
            <CardHeader>
              <CardTitle className="text-orange-700 dark:text-orange-400">Vehicles Above Threshold</CardTitle>
              <CardDescription>16+ Tickets in 12 Months</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold text-orange-900 dark:text-orange-100">
                {plates.length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="plates" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="plates">Vehicles (&gt;15 Tickets)</TabsTrigger>
            <TabsTrigger value="drivers">Drivers (&gt;11 Points)</TabsTrigger>
            <TabsTrigger value="recent">Recent (&gt;11 Points)</TabsTrigger>
            <TabsTrigger value="upload">Sandbox Upload</TabsTrigger>
            <TabsTrigger value="intelligence">✨ Intelligence</TabsTrigger>
          </TabsList>

          <TabsContent value="plates">
            {/* ... existing plate content ... */}
            <Card>
              <CardHeader>
                <CardTitle>Identified Vehicles</CardTitle>
                <CardDescription>Top offenders by ticket count</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Plate</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Tickets (12mo)</TableHead>
                      <TableHead>Last Ticket</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {plates.map((plate, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono font-bold">{plate.plate}</TableCell>
                        <TableCell>{plate.state}</TableCell>
                        <TableCell>
                          <Badge variant={plate.ticket_count > 20 ? "destructive" : "default"}>
                            {plate.ticket_count}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(plate.last_ticket).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Button size="icon" variant="ghost">
                            <Copy className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="drivers">
            {/* ... existing driver content ... */}
            <Card>
              <CardHeader>
                <CardTitle>Identified Drivers</CardTitle>
                <CardDescription>Drivers exceeding point threshold</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>License ID</TableHead>
                      <TableHead>Points (24mo)</TableHead>
                      <TableHead>Violations</TableHead>
                      <TableHead>Last Violation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {drivers.map((driver, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono">{driver.license_id}</TableCell>
                        <TableCell>
                          <Badge variant="destructive">
                            {driver.total_points}
                          </Badge>
                        </TableCell>
                        <TableCell>{driver.violation_count}</TableCell>
                        <TableCell>{new Date(driver.last_violation).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                    {drivers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center h-24 text-muted-foreground">
                          No drivers found matching criteria (or data issue).
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recent">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Recent Drivers Above Threshold (Oct 2025)</CardTitle>
                    <CardDescription>Drivers with 11+ points in the last recorded month.</CardDescription>
                  </div>
                  <Button size="sm" variant="outline" asChild>
                    <a href="http://localhost:8000/api/violators/drivers/recent/download">Download CSV</a>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>License ID</TableHead>
                      <TableHead>Points (Oct 25)</TableHead>
                      <TableHead>Violations</TableHead>
                      <TableHead>Last Violation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentDrivers.map((driver, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono">{driver.license_id}</TableCell>
                        <TableCell>
                          <Badge variant="destructive">
                            {driver.total_points}
                          </Badge>
                        </TableCell>
                        <TableCell>{driver.violation_count}</TableCell>
                        <TableCell>{new Date(driver.last_violation).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                    {recentDrivers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center h-24 text-muted-foreground">
                          No recent drivers above threshold found in October 2025.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="upload">
            <UploadSection />
          </TabsContent>

          <TabsContent value="intelligence">
            <IntelligenceSection />
          </TabsContent>
        </Tabs>

      </div>
    </div>
  );
}
