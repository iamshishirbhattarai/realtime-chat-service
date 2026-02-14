import { ApiError, NetworkError, ValidationError } from "./error";

export async function handleApiError(response: Response): Promise<never> {
  try {
    const errorData = await response.json();
    if (response.status === 422 && Array.isArray(errorData.detail)) {
      const validationErrors = errorData.detail as ValidationError[];
      const message = validationErrors
        .map((error) => `${error.loc[error.loc.length - 1]}: ${error.msg}`)
        .join(", ");
      throw new ApiError(message, response.status, validationErrors);
    }
    const message =
      typeof errorData.detail === "string"
        ? errorData.detail
        : "An unknown error occurred";
    throw new ApiError(message, response.status);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new NetworkError();
  }
}
