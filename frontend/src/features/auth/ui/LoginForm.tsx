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
    <div className="flex-1 w-full grid place-items-center">
      <div className="w-full max-w-md mx-auto my-auto ">
        <h1 className="text-center font-bold text-4xl text-[#1a1b1b] tracking-tight">
          Welcome to TryChat
        </h1>
        <p className="text-center text-[#767676] font-medium mt-2 mb-5">
          {" "}
          A practice to implement a real time chat service
        </p>
        {generalError && (
          <p className="text-center text-red-600 mb-2">{generalError}</p>
        )}

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-5 px-4 py-4 mx-auto"
        >
          <div className="flex flex-col gap-2">
            <label htmlFor="username" className="text-[#1f1f1f] font-medium">
              Email
            </label>
            <input
              type="text"
              id="username"
              placeholder="Enter Your Username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (fieldErrors.userName) {
                  setFieldErrors((prev) => ({ ...prev, userName: undefined }));
                }
              }}
              className="w-full border border-[#d5d5d5] rounded-lg p-2"
            />
            {fieldErrors.userName && (
              <p className="text-red-600">{fieldErrors.userName}</p>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-[#1f1f1f]">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter Your Password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: undefined }));
                }
              }}
              className="w-full border border-[#d5d5d5] rounded-lg p-2"
            />
            {fieldErrors.password && (
              <p className="text-red-600">{fieldErrors.password}</p>
            )}
          </div>
          <button
            type="submit"
            className="w-full border rounded-lg p-2 cursor-pointer bg-[#181a1c] text-white mt-2"
          >
            Login{" "}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LogInForm;
