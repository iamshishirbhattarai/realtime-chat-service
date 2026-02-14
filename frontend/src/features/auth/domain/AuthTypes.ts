//type of user credentials and auth user
export type UserCredentials = {
  username: string;
  password: string;
};

export type SignupResponse = {
  msg: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
