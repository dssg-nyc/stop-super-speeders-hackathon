"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, CheckCircle2, Download, UploadCloud } from "lucide-react";

export default function UploadSection() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://localhost:8000/api/upload/analyze", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed");
            }

            const data = await res.json();
            setResults(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const downloadTemplate = (type: "drivers" | "plates") => {
        window.open(`http://localhost:8000/api/upload/template/${type}`, "_blank");
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Upload Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <UploadCloud className="h-5 w-5" />
                            Sandbox Upload
                        </CardTitle>
                        <CardDescription>
                            Test your own data against the Super Speeder logic.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex flex-col space-y-2">
                            <Input type="file" accept=".csv" onChange={handleFileChange} />
                            <p className="text-xs text-muted-foreground">
                                Supported formats: .csv (Drivers or Plates)
                            </p>
                        </div>
                        <Button onClick={handleUpload} disabled={!file || loading} className="w-full">
                            {loading ? "Analyzing..." : "Analyze File"}
                        </Button>

                        {error && (
                            <div className="p-3 bg-red-100 text-red-700 text-sm rounded flex items-center gap-2">
                                <AlertCircle className="h-4 w-4" />
                                {error}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Templates Card */}
                <Card>
                    <CardHeader>
                        <CardTitle>Templates</CardTitle>
                        <CardDescription>Download CSV templates to format your data.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button variant="outline" className="w-full justify-start gap-2" onClick={() => downloadTemplate("drivers")}>
                            <Download className="h-4 w-4" />
                            Driver Violation Template
                        </Button>
                        <Button variant="outline" className="w-full justify-start gap-2" onClick={() => downloadTemplate("plates")}>
                            <Download className="h-4 w-4" />
                            Vehicle Ticket Template
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Results Area */}
            {results && (
                <Card className="border-green-200 bg-green-50/20">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-green-800">
                            <CheckCircle2 className="h-5 w-5" />
                            Analysis Complete
                        </CardTitle>
                        <CardDescription>
                            Identified <strong>{results.count}</strong> violators in uploaded file.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>ID</TableHead>
                                    <TableHead>Violations/Points</TableHead>
                                    <TableHead>Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {results.violators.map((v: any, i: number) => (
                                    <TableRow key={i}>
                                        <TableCell className="font-mono font-bold">
                                            {v.license_id || v.plate}
                                        </TableCell>
                                        <TableCell>
                                            {v.total_points ? `${v.total_points} Points` : `${v.ticket_count} Tickets`}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="destructive">Super Speeder</Badge>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
