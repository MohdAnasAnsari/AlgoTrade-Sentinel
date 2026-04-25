"use client";
import { useCallback, useEffect, useState } from "react";
import {
  AutoPromoteResult,
  ComparisonResult,
  ModelVersionInfo,
  PromoteRequest,
  RegistryLogEntry,
  registryApi,
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const DEFAULT_MODEL = "signal-predictor";

export function useModelRegistry(modelName = DEFAULT_MODEL) {
  const { pushToast } = useToast();
  const [champion,     setChampion]     = useState<ModelVersionInfo | null>(null);
  const [challengers,  setChallengers]  = useState<ModelVersionInfo[]>([]);
  const [allVersions,  setAllVersions]  = useState<ModelVersionInfo[]>([]);
  const [comparison,   setComparison]   = useState<ComparisonResult | null>(null);
  const [auditLog,     setAuditLog]     = useState<RegistryLogEntry[]>([]);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState<string | null>(null);

  // Promote modal
  const [promoteTarget, setPromoteTarget] = useState<ModelVersionInfo | null>(null);
  const [promoteNotes,  setPromoteNotes]  = useState("");
  const [promoting,     setPromoting]     = useState(false);
  const [promoteResult, setPromoteResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [versions, log] = await Promise.allSettled([
        registryApi.listVersions(modelName),
        registryApi.getLog(),
      ]);

      if (versions.status === "fulfilled") {
        const all = versions.value;
        setAllVersions(all);
        setChampion(all.find((v) => v.stage === "Production") ?? null);
        setChallengers(all.filter((v) => v.stage === "Staging"));
        setComparison({
          model_name:  modelName,
          champion:    all.find((v) => v.stage === "Production") ?? null,
          challengers: all.filter((v) => v.stage === "Staging"),
        });
      }
      if (log.status === "fulfilled") setAuditLog(log.value);
    } catch (e) {
      console.error("Registry load failed", e);
      setError(e instanceof Error ? e.message : "Failed to load the model registry.");
    } finally {
      setLoading(false);
    }
  }, [modelName]);

  useEffect(() => { load(); }, [load]);

  const promote = useCallback(async () => {
    if (!promoteTarget) return;
    setPromoting(true);
    try {
      await registryApi.promote(modelName, {
        version:     promoteTarget.version,
        notes:       promoteNotes,
        promoted_by: "user",
      });
      pushToast({
        title: "Model promoted",
        description: `Version ${promoteTarget.version} moved to Production.`,
        tone: "success",
      });
      setPromoteResult("Model promoted successfully");
      setPromoteTarget(null);
      setPromoteNotes("");
      await load();
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      setPromoteResult(`Promotion failed: ${err}`);
      setError(err);
      pushToast({
        title: "Promotion failed",
        description: err,
        tone: "error",
      });
    } finally {
      setPromoting(false);
    }
  }, [modelName, promoteTarget, promoteNotes, load, pushToast]);

  const archive = useCallback(async (version: string) => {
    try {
      await registryApi.archive(modelName, version);
      pushToast({
        title: "Version archived",
        description: `Version ${version} was archived.`,
        tone: "success",
      });
      await load();
    } catch (e) {
      console.error("Archive failed", e);
      setError(e instanceof Error ? e.message : "Archive failed.");
      pushToast({
        title: "Archive failed",
        description: e instanceof Error ? e.message : "Archive failed.",
        tone: "error",
      });
    }
  }, [modelName, load, pushToast]);

  const runAutoPromote = useCallback(async (): Promise<AutoPromoteResult | null> => {
    try {
      const result = await registryApi.autoPromote(modelName);
      pushToast({
        title: result.promoted ? "Auto-promotion succeeded" : "Auto-promotion check complete",
        description: result.message,
        tone: result.promoted ? "success" : "error",
      });
      if (result.promoted) await load();
      return result;
    } catch (e) {
      console.error("Auto-promote failed", e);
      setError(e instanceof Error ? e.message : "Auto-promotion failed.");
      pushToast({
        title: "Auto-promotion failed",
        description: e instanceof Error ? e.message : "Auto-promotion failed.",
        tone: "error",
      });
      return null;
    }
  }, [modelName, load, pushToast]);

  return {
    champion,
    challengers,
    allVersions,
    comparison,
    auditLog,
    loading,
    error,
    load,
    // Promote modal
    promoteTarget,
    setPromoteTarget,
    promoteNotes,
    setPromoteNotes,
    promoting,
    promote,
    promoteResult,
    setPromoteResult,
    archive,
    runAutoPromote,
  };
}
