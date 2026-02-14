import { handleApiError } from "@/src/shared/infra/api/apiClient";
import {
  LoginResponse,
  SignupResponse,
  UserCredentials,
} from "../domain/AuthTypes";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function signUpApi(
  data: UserCredentials,
): Promise<SignupResponse> {
  const payload = new URLSearchParams({
    username: data?.username,
    password: data?.password,
  });
  const response = await fetch(`${API_URL}/auth/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    credentials: "include",
    body: payload,
  });
  if (!response.ok) {
    await handleApiError(response);
  }
  return response.json();
}

export async function loginApi(data: UserCredentials): Promise<LoginResponse> {
  const payload = new URLSearchParams({
    username: data?.username,
    password: data?.password,
  });
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    credentials: "include",
    body: payload,
  });
  if (!response.ok) {
    await handleApiError(response);
  }
  return response.json();
}
