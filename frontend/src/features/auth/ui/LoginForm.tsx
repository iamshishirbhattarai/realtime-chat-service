"use client";
import React from "react";
import { loginApi } from "../infra/authApi";
import { ApiError, NetworkError } from "@/src/shared/infra/api/error";

const LogInForm = () => {
  const [username, setUsername] = React.useState<string>("");
  const [password, setPassword] = React.useState<string>("");
  const [fieldErrors, setFieldErrors] = React.useState<{
    userName?: string;
    password?: string;
  }>({});
  const [generalError, setGeneralError] = React.useState<string>("");
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await loginApi({ username, password });
      console.log("Log in successful", response);
      setGeneralError("");
      setFieldErrors({});
    } catch (error) {
      console.error("Log in failed", error);
      if (error instanceof ApiError) {
        if (error?.statusCode === 422 && error?.validationErrors) {
          const errors: { userName?: string; password?: string } = {};
          error.validationErrors.forEach((validationError) => {
            const field = validationError.loc[validationError.loc.length - 1];
            if (field === "username") {
              errors.userName = validationError.msg;
            } else if (field === "password") {
              errors.password = validationError.msg;
            }
          });
          setFieldErrors(errors);
        } else {
          setGeneralError(error.message);
        }
      } else if (error instanceof NetworkError) {
        setGeneralError(
          "Cannot connect to server. Please check your connection.",
        );
      } else {
        setGeneralError("An unexpected error occurred. Please try again.");
      }
    }
  };
  return (
    <div className="w-fit border grid place-items-center ">
      <h1 className="text-center">LogInForm</h1>
      {generalError && <p className="text-red-500">{generalError}</p>}

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 w-fit px-4 py-4"
      >
        <input
          type="text"
          placeholder="username"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value);
            if (fieldErrors.userName) {
              setFieldErrors((prev) => ({ ...prev, userName: undefined }));
            }
          }}
          className="w-40 border rounded-sm p-2"
        />
        {fieldErrors.userName && (
          <p className="text-red-500">{fieldErrors.userName}</p>
        )}
        <input
          type="password"
          placeholder="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) {
              setFieldErrors((prev) => ({ ...prev, password: undefined }));
            }
          }}
          className="w-40 border rounded-sm p-2"
        />
        {fieldErrors.password && (
          <p className="text-red-500">{fieldErrors.password}</p>
        )}
        <button
          type="submit"
          className="w-40 border rounded-sm p-2 cursor-pointer"
        >
          Sign Up
        </button>
      </form>
    </div>
  );
};

export default LogInForm;
