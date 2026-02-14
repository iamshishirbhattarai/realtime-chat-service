export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public validationErrors?: ValidationError[],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export class NetworkError extends Error {
  constructor(message?: "Network Error") {
    super(message);
    this.name = "NetworkError";
  }
}
