"use client";

import * as React from "react";
import { trackError } from "@/lib/analytics";
import { classifyError } from "@/lib/errors";

type ErrorBoundaryProps = {
  children: React.ReactNode;
  title?: string;
  description?: string;
  onReset?: () => void;
  resetLabel?: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error: Error | null;
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error(error);
    trackError(error, {
      source: "ErrorBoundary.componentDidCatch",
      component: this.constructor.name,
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const classified = this.state.error ? classifyError(this.state.error) : null;
    const title = this.props.title ?? "Something went wrong";
    const description =
      this.props.description ??
      "The page had an unexpected problem. You can try again.";
    const categoryStyles: Record<string, string> = {
      network: "border-yellow-200 bg-yellow-50",
      contract: "border-orange-200 bg-orange-50",
      wallet: "border-blue-200 bg-blue-50",
      validation: "border-amber-200 bg-amber-50",
      authentication: "border-purple-200 bg-purple-50",
      business_logic: "border-indigo-200 bg-indigo-50",
      system: "border-red-200 bg-red-50",
      user: "border-gray-200 bg-gray-50",
      unknown: "border-red-200 bg-red-50",
    };

    const categoryTextStyles: Record<string, string> = {
      network: "text-yellow-900",
      contract: "text-orange-900",
      wallet: "text-blue-900",
      validation: "text-amber-900",
      authentication: "text-purple-900",
      business_logic: "text-indigo-900",
      system: "text-red-900",
      user: "text-gray-900",
      unknown: "text-red-900",
    };

    const category = classified?.category ?? "unknown";
    return (
      <div
        className={`rounded-xl border p-6 text-center ${categoryStyles[category] ?? categoryStyles.unknown}`}
      >
        <p className={`text-sm font-semibold ${categoryTextStyles[category] ?? categoryTextStyles.unknown}`}>
          {classified?.title ?? title}
        </p>
        <p className="mt-1 text-sm text-red-700">{classified?.message ?? description}</p>
        {this.state.error?.message ? (
          <p className="mt-2 text-xs text-red-700 break-words">{this.state.error.message}</p>
        ) : null}
        <div className="mt-5 flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={this.handleReset}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
          >
            {this.props.resetLabel ?? "Try again"}
          </button>
        </div>
      </div>
    );
  }
}
