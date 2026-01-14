"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { ChevronLeft, ChevronRight, FileText, Download, Loader2, Plus, Trash2, ArrowUp, ArrowDown } from "lucide-react";
import { api } from "@/lib/api";

interface TableConfig {
  type: string;
  title: string;
  columns: string[];
  page_break_after: boolean;
}

interface AvailableTable {
  name: string;
  columns: string[];
}

interface AdditionalTableConfig extends TableConfig {
  id: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
}

export default function CustomReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [availableTables, setAvailableTables] = useState<Record<string, AvailableTable>>({});
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeExecutiveSummary, setIncludeExecutiveSummary] = useState(true);
  const [outputFormat, setOutputFormat] = useState<'pdf' | 'docx'>('pdf');
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [tableConfigs, setTableConfigs] = useState<Record<string, TableConfig>>({});
  const [additionalTables, setAdditionalTables] = useState<AdditionalTableConfig[]>([]);

  const availableTableTypes = Object.keys(availableTables);

  useEffect(() => {
    loadProjects();
    
    // Check if project is pre-selected from URL
    const projectId = searchParams.get('project');
    if (projectId) {
      setSelectedProjectId(projectId);
      loadAvailableColumns(projectId);
      setStep(2); // Skip to step 2 if project is pre-selected
    }
  }, [searchParams]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await api.getProjects();
      setProjects(response);
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableColumns = async (projectId: string) => {
    try {
      const response = await api.getAvailableReportColumns(projectId);
      setAvailableTables(response);
    } catch (error) {
      console.error("Failed to load available columns:", error);
    }
  };

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId);
    setSelectedTables([]);
    setTableConfigs({});
    setAdditionalTables([]);
    loadAvailableColumns(projectId);
  };

  const createTableConfigFromType = (tableType: string): TableConfig => {
    const table = availableTables[tableType];
    return {
      type: tableType,
      title: table?.name || tableType,
      columns: table?.columns ? [...table.columns] : [],
      page_break_after: false,
    };
  };

  const handleTableToggle = (tableType: string, checked: boolean) => {
    if (checked) {
      setSelectedTables([...selectedTables, tableType]);
      // Initialize with all columns selected
      const table = availableTables[tableType];
      if (table) {
        setTableConfigs({
          ...tableConfigs,
          [tableType]: {
            type: tableType,
            title: table.name,
            columns: [...table.columns],
            page_break_after: false,
          },
        });
      }
    } else {
      setSelectedTables(selectedTables.filter((t: string) => t !== tableType));
      const newConfigs = { ...tableConfigs };
      delete newConfigs[tableType];
      setTableConfigs(newConfigs);
    }
  };

  const handleColumnToggle = (tableType: string, column: string, checked: boolean) => {
    const config = tableConfigs[tableType];
    if (!config) return;

    const newColumns = checked
      ? [...config.columns, column]
      : config.columns.filter((c: string) => c !== column);

    setTableConfigs({
      ...tableConfigs,
      [tableType]: {
        ...config,
        columns: newColumns,
      },
    });
  };

  const handleTitleChange = (tableType: string, title: string) => {
    const config = tableConfigs[tableType];
    if (!config) return;

    setTableConfigs({
      ...tableConfigs,
      [tableType]: {
        ...config,
        title,
      },
    });
  };

  const getAllAvailableColumns = (): string[] => {
    const allColumns = new Set<string>();
    Object.values(availableTables).forEach((table) => {
      table.columns.forEach((col) => allColumns.add(col));
    });
    // Remove redundant columns - Activity and Type are consolidated as Activity Type
    const filtered = Array.from(allColumns)
      .filter((col) => col !== 'Activity' && col !== 'Type')
      .sort();
    return filtered;
  };

  const handleAddAdditionalTable = () => {
    const allColumns = getAllAvailableColumns();
    setAdditionalTables([
      ...additionalTables,
      {
        id:
          typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random()}`,
        type: "custom",
        title: "",
        columns: allColumns,
        page_break_after: false,
      },
    ]);
  };

  const handleAdditionalColumnToggle = (id: string, column: string, checked: boolean) => {
    setAdditionalTables((prev) =>
      prev.map((table) => {
        if (table.id !== id) return table;
        const newColumns = checked
          ? Array.from(new Set([...table.columns, column]))
          : table.columns.filter((c) => c !== column);
        return { ...table, columns: newColumns };
      })
    );
  };

  const handleAdditionalTitleChange = (id: string, title: string) => {
    setAdditionalTables((prev) =>
      prev.map((table) => (table.id === id ? { ...table, title } : table))
    );
  };

  const handleAdditionalPageBreakToggle = (id: string, checked: boolean) => {
    setAdditionalTables((prev) =>
      prev.map((table) => (table.id === id ? { ...table, page_break_after: checked } : table))
    );
  };

  const handleRemoveAdditionalTable = (id: string) => {
    setAdditionalTables((prev) => prev.filter((table) => table.id !== id));
  };

  const handleMoveColumn = (id: string, columnIndex: number, direction: "up" | "down") => {
    setAdditionalTables((prev) =>
      prev.map((table) => {
        if (table.id !== id) return table;
        const newColumns = [...table.columns];
        const newIndex = direction === "up" ? columnIndex - 1 : columnIndex + 1;
        
        if (newIndex >= 0 && newIndex < newColumns.length) {
          [newColumns[columnIndex], newColumns[newIndex]] = [newColumns[newIndex], newColumns[columnIndex]];
        }
        
        return { ...table, columns: newColumns };
      })
    );
  };

  const handlePageBreakToggle = (tableType: string, checked: boolean) => {
    const config = tableConfigs[tableType];
    if (!config) return;

    setTableConfigs({
      ...tableConfigs,
      [tableType]: {
        ...config,
        page_break_after: checked,
      },
    });
  };

  const generateReport = async () => {
    if (!selectedProjectId) return;

    try {
      setGenerating(true);

      const baseTables = selectedTables
        .map((tableType: string) => tableConfigs[tableType])
        .filter(Boolean);
      const extraTables = additionalTables.map(({ id, ...rest }) => rest);
      const allTables = [...baseTables, ...extraTables];
      
      const reportConfig = {
        format_type: "custom",
        output_format: outputFormat,
        include_charts: includeCharts,
        include_executive_summary: includeExecutiveSummary,
        tables: allTables,
      };

      const blob = await api.downloadReport(selectedProjectId, reportConfig);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `custom_report_${selectedProjectId}.${outputFormat}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert("Failed to generate report. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const canProceedToStep2 = selectedProjectId && Object.keys(availableTables).length > 0;
  const canProceedToStep3 = selectedTables.length > 0 || additionalTables.length > 0;
  const canGenerate =
    selectedProjectId &&
    (includeExecutiveSummary || includeCharts || selectedTables.length > 0 || additionalTables.length > 0);

  const selectedTableConfigs = selectedTables
    .map((tableType: string) => tableConfigs[tableType])
    .filter(Boolean);
  const combinedTables = [...selectedTableConfigs, ...additionalTables];

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <Button variant="ghost" onClick={() => router.push("/reports")}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back to Reports
        </Button>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Custom Report Builder</h1>
        <p className="text-muted-foreground">
          Create a customized carbon footprint report by selecting tables and columns
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center mb-8 gap-4">
        <div className={`flex items-center ${step >= 1 ? "text-primary" : "text-muted-foreground"}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step >= 1 ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}>
            1
          </div>
          <span className="ml-2 hidden sm:inline">Select Project</span>
        </div>
        <div className="h-px w-12 bg-muted" />
        <div className={`flex items-center ${step >= 2 ? "text-primary" : "text-muted-foreground"}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step >= 2 ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}>
            2
          </div>
          <span className="ml-2 hidden sm:inline">Configure Tables</span>
        </div>
        <div className="h-px w-12 bg-muted" />
        <div className={`flex items-center ${step >= 3 ? "text-primary" : "text-muted-foreground"}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step >= 3 ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}>
            3
          </div>
          <span className="ml-2 hidden sm:inline">Preview & Generate</span>
        </div>
      </div>

      {/* Step 1: Project Selection */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Select Project</CardTitle>
            <CardDescription>Choose the project you want to generate a report for</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <div className="grid gap-4">
                {projects.map((project: Project) => (
                  <Card
                    key={project.id}
                    className={`cursor-pointer transition-colors ${
                      selectedProjectId === project.id
                        ? "border-primary bg-primary/5"
                        : "hover:border-muted-foreground"
                    }`}
                    onClick={() => handleProjectSelect(project.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold">{project.name}</h3>
                          <p className="text-sm text-muted-foreground">{project.description}</p>
                        </div>
                        {selectedProjectId === project.id && (
                          <div className="h-5 w-5 rounded-full bg-primary flex items-center justify-center">
                            <svg className="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
            <div className="flex justify-end mt-6">
              <Button onClick={() => setStep(2)} disabled={!canProceedToStep2}>
                Next: Configure Tables
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Table Configuration */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 2: Configure Report Sections</CardTitle>
            <CardDescription>Select tables and customize columns to include</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* General Options */}
            <div className="space-y-4 pb-4 border-b">
              <h3 className="font-semibold">General Options</h3>
              <div className="flex items-center justify-between">
                <Label htmlFor="exec-summary">Include Executive Summary</Label>
                <Switch
                  id="exec-summary"
                  checked={includeExecutiveSummary}
                  onCheckedChange={setIncludeExecutiveSummary}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="charts">Include Visualizations & Charts</Label>
                <Switch id="charts" checked={includeCharts} onCheckedChange={setIncludeCharts} />
              </div>
            </div>

            {/* Table Selection */}
            <div className="space-y-4">
              <h3 className="font-semibold">Select Tables</h3>
              {Object.entries(availableTables).map(([tableType, table]: [string, AvailableTable]) => (
                <Card key={tableType} className="overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={tableType}
                        checked={selectedTables.includes(tableType)}
                        onCheckedChange={(checked) => handleTableToggle(tableType, checked as boolean)}
                      />
                      <Label htmlFor={tableType} className="cursor-pointer font-medium">
                        {table.name}
                      </Label>
                    </div>
                  </CardHeader>

                  {selectedTables.includes(tableType) && (
                    <CardContent className="space-y-4 pt-0">
                      <div className="space-y-2">
                        <Label>Custom Title (optional)</Label>
                        <Input
                          placeholder={table.name}
                          value={tableConfigs[tableType]?.title || ""}
                          onChange={(e) => handleTitleChange(tableType, e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Select Columns</Label>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {table.columns.map((column) => (
                            <div key={column} className="flex items-center space-x-2">
                              <Checkbox
                                id={`${tableType}-${column}`}
                                checked={tableConfigs[tableType]?.columns.includes(column) || false}
                                onCheckedChange={(checked) =>
                                  handleColumnToggle(tableType, column, checked as boolean)
                                }
                              />
                              <Label
                                htmlFor={`${tableType}-${column}`}
                                className="text-sm cursor-pointer"
                              >
                                {column}
                              </Label>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`${tableType}-pagebreak`}
                          checked={tableConfigs[tableType]?.page_break_after || false}
                          onCheckedChange={(checked) =>
                            handlePageBreakToggle(tableType, checked as boolean)
                          }
                        />
                        <Label htmlFor={`${tableType}-pagebreak`} className="text-sm cursor-pointer">
                          Add page break after this table
                        </Label>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>

            {/* Additional Tables */}
            <div className="space-y-4 pt-2 border-t">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Add Additional Tables</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAddAdditionalTable}
                  disabled={availableTableTypes.length === 0}
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Add table
                </Button>
              </div>

              {additionalTables.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Add another table and pick any columns from the available sets.
                </p>
              ) : (
                additionalTables.map((table) => {
                  const tableOption = availableTables[table.type];
                  return (
                    <Card key={table.id} className="border-dashed">
                      <CardContent className="space-y-4 pt-4">
                        <div className="flex items-start justify-between">
                          <div className="space-y-2 w-full">
                            <Label htmlFor={`table-title-${table.id}`}>Table Name</Label>
                            <Input
                              id={`table-title-${table.id}`}
                              placeholder="Enter table name (e.g., Activity Summary)"
                              value={table.title || ""}
                              onChange={(e) => handleAdditionalTitleChange(table.id, e.target.value)}
                            />
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveAdditionalTable(table.id)}
                            className="self-start ml-2"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Remove
                          </Button>
                        </div>

                        <div className="space-y-3">
                          <Label>Select & Arrange Columns</Label>
                            <p className="text-xs text-muted-foreground">Check columns to include, use arrows to reorder</p>
                          
                            {/* Selected Columns List for Reordering */}
                            {table.columns.length > 0 && (
                              <div className="space-y-2 p-2 bg-primary/5 border border-primary/20 rounded-md">
                                <p className="text-xs font-medium text-primary">Selected Columns (in order):</p>
                                <div className="space-y-1">
                                  {table.columns.map((column, idx) => (
                                    <div key={`${table.id}-selected-${column}`} className="flex items-center justify-between gap-2 p-2 bg-white/50 rounded border border-gray-200">
                                      <span className="text-sm font-medium">{idx + 1}. {column}</span>
                                      <div className="flex gap-1">
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          className="h-6 w-6 p-0"
                                          onClick={() => handleMoveColumn(table.id, idx, "up")}
                                          disabled={idx === 0}
                                          title="Move up"
                                        >
                                          <ArrowUp className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          className="h-6 w-6 p-0"
                                          onClick={() => handleMoveColumn(table.id, idx, "down")}
                                          disabled={idx === table.columns.length - 1}
                                          title="Move down"
                                        >
                                          <ArrowDown className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="h-6 w-6 p-0 text-destructive"
                                          onClick={() => handleAdditionalColumnToggle(table.id, column, false)}
                                          title="Remove"
                                        >
                                          <Trash2 className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          
                            {/* Available Columns to Add */}
                            <div className="space-y-2">
                              <p className="text-xs font-medium">Available Columns:</p>
                              <div className="space-y-2 max-h-60 overflow-y-auto border rounded-md p-3 bg-muted/30">
                                {getAllAvailableColumns().map((column) => {
                                  const isSelected = table.columns.includes(column);
                                  return (
                                    <div key={`${table.id}-available-${column}`} className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`${table.id}-${column}`}
                                        checked={isSelected}
                                        onCheckedChange={(checked) =>
                                          handleAdditionalColumnToggle(table.id, column, checked as boolean)
                                        }
                                      />
                                      <Label
                                        htmlFor={`${table.id}-${column}`}
                                        className="text-sm cursor-pointer"
                                      >
                                        {column}
                                      </Label>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id={`${table.id}-pagebreak`}
                            checked={table.page_break_after || false}
                            onCheckedChange={(checked) =>
                              handleAdditionalPageBreakToggle(table.id, checked as boolean)
                            }
                          />
                          <Label htmlFor={`${table.id}-pagebreak`} className="text-sm cursor-pointer">
                            Add page break after this table
                          </Label>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>

            <div className="flex justify-between mt-6">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={() => setStep(3)} disabled={!canProceedToStep3}>
                Next: Preview & Generate
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Preview & Generate */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 3: Preview & Generate Report</CardTitle>
            <CardDescription>Review your selections and generate the custom report</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <h3 className="font-semibold">Report Configuration Summary</h3>
              
              <div className="bg-muted p-4 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Project:</span>
                  <span className="text-sm font-medium">
                    {projects.find((p) => p.id === selectedProjectId)?.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Executive Summary:</span>
                  <span className="text-sm font-medium">{includeExecutiveSummary ? "Yes" : "No"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Visualizations:</span>
                  <span className="text-sm font-medium">{includeCharts ? "Yes" : "No"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Number of Tables:</span>
                  <span className="text-sm font-medium">{combinedTables.length}</span>
                </div>
              </div>

              {/* Output Format Selection */}
              <div className="space-y-3 pt-4 border-t">
                <h4 className="text-sm font-medium">Output Format</h4>
                <div className="flex gap-3">
                  <Button
                    variant={outputFormat === 'pdf' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setOutputFormat('pdf')}
                    className="flex-1"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    PDF
                  </Button>
                  <Button
                    variant={outputFormat === 'docx' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setOutputFormat('docx')}
                    className="flex-1"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    DOCX (Word)
                  </Button>
                </div>
              </div>

              {combinedTables.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium">Selected Tables:</h4>
                  {combinedTables.map((config, index) => (
                    <div key={`${config.type}-${config.title || index}`} className="bg-muted p-3 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-sm">
                            {index + 1}. {config.title || config.type}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Columns: {config.columns.join(", ")}
                          </div>
                        </div>
                        {config.page_break_after && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                            Page Break
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-between mt-6">
              <Button variant="outline" onClick={() => setStep(2)}>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button
                onClick={generateReport}
                disabled={!canGenerate || generating}
                className="gap-2"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Generate as {outputFormat.toUpperCase()}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
