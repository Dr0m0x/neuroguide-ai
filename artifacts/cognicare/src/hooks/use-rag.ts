import { api } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function useSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: api.getSessions,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => api.createSession(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

export function useDeleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

export function useMessages(sessionId?: string) {
  return useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => api.getMessages(sessionId!),
    enabled: !!sessionId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.sendMessage,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['messages', variables.session_id] });
    },
  });
}

export function useTopics() {
  return useQuery({
    queryKey: ['topics'],
    queryFn: api.getTopics,
  });
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: api.getStats,
  });
}

export function useHealthz() {
  return useQuery({
    queryKey: ['healthz'],
    queryFn: api.getHealthz,
  });
}
